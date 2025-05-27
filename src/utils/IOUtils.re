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
