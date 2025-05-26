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
