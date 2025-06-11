let toPromise: 'a. IO.t('a, Js.Exn.t) => Js.Promise.t('a) =
  io =>
    Js.Promise.make((~resolve, ~reject) =>
      io
      |> IO.unsafeRunAsync(
           fun
           | Ok(v) => resolve(. v)
           | Error(e) => reject(. RJs.Exn.unsafeToExn(e)),
         )
    );

/**
Converts a Promise to IO (with no logging)
*/
let fromPromise:
  'a 'e.
  (Js.Promise.error => 'e, unit => Js.Promise.t('a)) => IO.t('a, 'e)
 =
  (promiseErrorToError, runPromise) =>
    IO.async(onDone =>
      runPromise()
      |> Js.Promise.then_(a => Js.Promise.resolve(onDone(Ok(a))))
      |> Js.Promise.catch(e =>
           Js.Promise.resolve(onDone(Error(e |> promiseErrorToError)))
         )
      |> ignore
    );

external unsafePromiseToExn: Js.Promise.error => Js.Exn.t = "%identity";

/**
Converts a Promise to IO with a Js.Exn.t error type (with no logging)
*/
let fromPromiseWithJsExn:
  'a.
  (unit => Js.Promise.t('a)) => IO.t('a, Js.Exn.t)
 =
  lazyPromise => fromPromise(unsafePromiseToExn, lazyPromise);

/**
   Be warned, the default traverse/sequence implementations for IO and LogIO
   are not stack-safe and will explode your computer if you have a big list
   of IOs.

   See [List.Concurrent] or [List.Sequential] for alternate (more) stack-safe
   implementations of Traversable over lists.
   */
module List = {
  /**
For backwards compatbility - remove someday
*/
  let toIO: IO.t('a, 'e) => IO.t('a, 'e) = id;

  /**
For backwards compatbility - remove someday
*/
  let fromIO: IO.t('a, 'e) => IO.t('a, 'e) = id;

  let traverse =
      (type e, f: 'a => IO.t('b, e), list: list('a)): IO.t(list('b), e) => {
    module LogIoE =
      IO.WithError({
        type t = e;
      });
    module TraverseIO = Relude.List.Traversable(LogIoE.Applicative);
    TraverseIO.traverse(f, list);
  };

  let sequence = (type e, xs: list(IO.t('a, e))): IO.t(list('a), e) => {
    module LogIoE =
      IO.WithError({
        type t = e;
      });
    module TraverseIO = Relude.List.Traversable(LogIoE.Applicative);
    TraverseIO.sequence(xs);
  };

  let%private moreStackSafeSequence:
    (int, list(IO.t('ok, 'err))) => IO.t(list('ok), 'err) =
    (chunkSize, list) =>
      IO.async(onDone => {
        let oks = ref([]);
        let err = ref(None);

        let tryDone = () => {
          let oks = oks^;
          let err = err^;

          switch (err) {
          | Some(err) => onDone(Error(err))
          | None
              when
                Relude.List.length(oks) |> Int.eq(list |> Relude.List.length) =>
            onDone(Ok(oks))
          | None => ()
          };
        };

        let onSomeDone = list => {
          oks :=
            list
            |> Relude.List.map(Result.getOk)
            |> Relude.List.catOptions
            |> Relude.List.concat(oks^);
          err :=
            list
            |> Relude.List.map(Result.getError)
            |> Relude.List.catOptions
            |> Relude.List.head;
          tryDone();
          ();
        };

        list
        |> Relude.List.map(toIO)
        |> Relude.List.chunk(chunkSize |> Int.clamp(~min=1, ~max=3))
        |> Relude.List.foldLeft(
             const(
               fun
               | [a, b, c] =>
                 IO.unsafeRunAsyncPar3(
                   (a, b, c) => onSomeDone([a, b, c]),
                   a,
                   b,
                   c,
                 )
               | [a, b] =>
                 IO.unsafeRunAsyncPar2((a, b) => onSomeDone([a, b]), a, b)
               | [a] => IO.unsafeRunAsync(a => onSomeDone([a]), a)
               | _ => (),
             ),
             (),
           );
        ();
      })
      |> fromIO;

  /**
     Run a list of LogIOs with max concurrency (3) until the list is exhausted.

     This implementation will be obsoleted by a stack-safe [IO] implementation,
     but has to exist for now because the default Apply instance for IO is not stack-safe
     and may cause stack overflow exceptions on unbounded lists.

     [Concurrent] or [Sequential] may make sensible defaults until Relude's IO is
     implemented in stack-safe manner, but it's worth noting that if you
     are encountering stack overflows with IOs, you should strongly consider
     bounding the list to a smaller scope.
     */
  module Concurrent = {
    let sequence = (type e, xs: list(IO.t('a, e))): IO.t(list('a), e) => {
      moreStackSafeSequence(3, xs);
    };

    let traverse =
        (type e, f: 'a => IO.t('b, e), xs: list('a)): IO.t(list('b), e) => {
      xs |> Relude.List.map(f) |> sequence;
    };

    let runEach = (type e, xs: list(IO.t(unit, e))): IO.t(unit, e) =>
      xs |> sequence |> IO.map(ignore);

    let forEach =
        (type e, f: 'a => IO.t(unit, e), xs: list('a)): IO.t(unit, e) =>
      xs |> traverse(f) |> IO.map(ignore);
  };

  /**
     Run a list of LogIOs in sequence until the list is exhausted.

     If you have not read the documentation for the sister module [`Concurrent`],
     do so now.
     */
  module Sequential = {
    let sequence = (type e, xs: list(IO.t('a, e))): IO.t(list('a), e) => {
      moreStackSafeSequence(1, xs);
    };

    let traverse =
        (type e, f: 'a => IO.t('b, e), list: list('a)): IO.t(list('b), e) => {
      list |> Relude.List.map(f) |> sequence;
    };
  };
};
