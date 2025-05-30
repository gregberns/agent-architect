module ParseError = BsDecode.Decode.ParseError;

let parseSafe = str =>
  Result.tries(() => Js.Json.parseExn(str)) |> Result.toOption;

module Decode = {
  include BsDecode.Decode.AsResult.OfParseError;

  type t('a) = Js.Json.t => Result.t('a, ParseError.failure);

  // This is a sneak preview of what's coming in the next release of bs-decode,
  // which will replace the need for `variantFromJson` and similar functions.
  // At the moment, the provided validation function has to produce one of the
  // underlying error constructors (e.g. `ExpectedValidOption`), but in the
  // future, this will accept any polymorphic variant you can dream of.
  let validate = (f, decode) =>
    decode
    |> flatMap((a, json) =>
         a |> f |> Result.mapError(x => ParseError.Val(x, json))
       );

  let intFromNumberOrString = {
    let intFromString =
      string |> validate(Int.fromString >> Result.fromOption(`ExpectedInt));
    oneOf(intFromNumber, [intFromString]);
  };

  let floatFromNumberOrString = {
    let floatFromString =
      string
      |> validate(Float.fromString >> Result.fromOption(`ExpectedNumber));
    oneOf(floatFromNumber, [floatFromString]);
  };

  let stringFromStringOrInt =
    oneOf(string, [intFromNumber |> map(Int.toString)]);

  let stringFromStringOrFloat =
    oneOf(string, [floatFromNumber |> map(Float.toString)]);

  /**
  [jsonFromString] attempts to decode the provided JSON as a string, then the
  string is parsed as JSON again.
  */
  let jsonFromString =
    string |> validate(parseSafe >> Result.fromOption(`ExpectedValidOption));

  /**
  [jsonFromStringOrJson] attempts to decode the provided JSON as a string, which
  is then parsed back into JSON. If that fails, it falls back to the provided
  JSON value.
  */
  let jsonFromStringOrJson = oneOf(jsonFromString, [okJson]);

  let ior =
    fun
    | (Ok(a), Ok(b)) => Ior.both(a, b) |> Result.ok
    | (Ok(a), Error(_)) => Ior.this(a) |> Result.ok
    | (Error(_), Ok(b)) => Ior.that(b) |> Result.ok
    | (Error(errorA), Error(errorB)) =>
      ParseError.TriedMultiple(Nel.make(errorA, [errorB])) |> Result.error;

  /**
  [ior] attempts two decoders given the same JSON and returns an [Ior]
  representing whether either or both decoders succeeded.
  */
  let ior = (decodeA, decodeB, json) =>
    (json |> decodeA, json |> decodeB) |> ior;

  // No one should use this directly. Some would say we shouldn't be using this
  // at all. This captures all of the weird stuff we do to validate dates,
  // including a lot of effort spent handling values that couldn't possibly
  // exist in JSON (like date objects, Infinitiy, NaN).
  //
  // Technically, none of these cases should be possible. My best guess is that
  // we're using some library (pg? graphile-worker?) that gives us back JS
  // objects (not actually JSON), which we want to run through our normal
  // decoders, so we have to do all this extra work to handle non-JSON nonsense.
  //
  // It would be better to convert those JS objects back into valid JSON at the
  // source, before trying to run them through the decoders. But I'm not even
  // sure where to find "the source" and even if I could find it, I'm not sure
  // I'd be brave enough to change something so fragile.
  //
  // - mm, 2023-07-06
  module DateObj: {
    let date: t(Js.Date.t);
  } = {
    // Some dates come back as pos/neg infinity so we have to special case those
    let infinityToMaxDate = json => {
      let positiveInfinity: Js.Json.t = {%mel.raw | Infinity |};

      // We won't have to worry about this value for a little bit...
      let maxDate: Js.Date.t = {%mel.raw | new Date('3000-01-01') |};

      json === positiveInfinity
        ? maxDate |> Result.pure
        : Result.error(ParseError.Val(`ExpectedValidDate, json));
    };

    let negativeInfinityToMinDate = json => {
      let negativeInfinity: Js.Json.t = {%mel.raw | -Infinity |};

      // We don't expect anything to happen in the BCE
      let minDate: Js.Date.t = {%mel.raw | new Date('0000-01-01') |};

      json === negativeInfinity
        ? minDate |> Result.pure
        : Result.error(ParseError.Val(`ExpectedValidDate, json));
    };

    let isValidDate: Js.Json.t => bool =
      {%mel.raw |
        function isValidDate(date) {
          return date && Object.prototype.toString.call(date) === "[object Date]" && !isNaN(date);
        }
      |};

    external jsonDateToDate: Js.Json.t => Js.Date.t = "%identity";

    let jsonDateToDate = json =>
      json |> isValidDate ? json |> jsonDateToDate |> Option.pure : None;

    let toDate = maybeDate =>
      maybeDate
      |> jsonDateToDate
      |> Result.fromOption(ParseError.Val(`ExpectedValidDate, maybeDate));

    // try the date decoder from bs-decode, then check for a js date object,
    // then recover from positive and negative infinity for some reason, and
    // finally, map the error to a single `ExpectedValidDate` instead of the
    // `TriedMultiple` error which is just noisy and useless in this case
    let date = json =>
      json
      |> oneOf(date, [toDate, infinityToMaxDate, negativeInfinityToMinDate])
      |> Result.mapError(_ => ParseError.Val(`ExpectedValidDate, json));
  };

  // This shadows bs-decode's `date` decoder with our own, which handles a whole
  // bunch of extra cases that can't actually occur in JSON.
  let date = DateObj.date;

  // The following infix functions should be removed because they're shadowing
  // the infix functions from bs-decode (which do a better job of collecting all
  // errors, while these only preserve the last error).

  let (<$>) = Result.map;
  let (<*>) = Result.apply;
  let (<|>) = Result.alt;

  // The following functions are just re-exports of deprecated functions from
  // bs-decode so that we can control the deprecation warnings from a single
  // place. Eventually, we'll want to fix the deprecated uses and remove these.

  [@ocaml.warning "-3"]
  let variantFromString = variantFromString;

  [@ocaml.warning "-3"]
  let variantFromInt = variantFromInt;

  // I suspect this should be deprecated. There can't be that many places that
  // are actually interested in stringifying the inner error, and those places
  // can probably just do their own `mapError`
  let mapErrorToDebugString = result =>
    result |> Result.mapError(ParseError.failureToDebugString);
};

module Encode = {
  type encoder('a) = 'a => Js.Json.t;

  external null: Js.Json.t = "null";
  external string: string => Js.Json.t = "%identity";
  external floatToNumber: float => Js.Json.t = "%identity";
  external int: int => Js.Json.t = "%identity";
  external dict: Js.Dict.t(Js.Json.t) => Js.Json.t = "%identity";
  external boolean: bool => Js.Json.t = "%identity";

  let char = Char.code >> String.fromCharCode >> string;

  let date = Js.Date.toJSONUnsafe >> string;

  let optional = encode =>
    fun
    | None => null
    | Some(v) => encode(v);

  /**
  Given a field name, an encoder for the inner value, and an optional value,
  this returns an option of a key/value tuple. The idea is that you will create
  a list of many of these, run it through `catOptions` to filter out the `None`
  values, then pass it into `object_` to construct a JSON object.

  This approach will remove the actual keys from the object if the value is None
  instead of passing a `null` value. This can be important for constructing
  PATCH requests that treat null values differently from omitted fields.

  ```
  [
    optionalField("name", string, Some("Alice")),
    optionalField("date", date, None)
  ]
  |> List.catOptions
  |> object_ // { "name": "Alice" }
  ```
  */
  let optionalField = (fieldName: string, encode) =>
    Option.map(encode >> Tuple.make(fieldName));

  /**
  Given a field name, an encoder for the inner value, and a value, this returns
  an option of a key/value tuple that is always Some. This is meant to pair
  nicely with [optionalField] to produce a list of tuples of key/value pairs,
  where the [None] values can be filtered out before passing the whole thing to
  the [object_] encoder.
  */
  let someField = (fieldName: string, encode) =>
    encode >> Tuple.make(fieldName) >> Option.pure;

  let withDefault = (d, encode) =>
    fun
    | None => d
    | Some(v) => encode(v);

  let object_ = Js.Dict.fromList >> dict;

  external jsonArray: array(Js.Json.t) => Js.Json.t = "%identity";
  let array = encode => Array.map(encode) >> jsonArray;
  let arrayOf = array;
  let list = encode => List.toArray >> array(encode);

  let pair = (encodeA, encodeB, (a, b)) =>
    jsonArray([|encodeA(a), encodeB(b)|]);
  let tuple2 = pair;
  let tuple3 = (encodeA, encodeB, encodeC, (a, b, c)) =>
    jsonArray([|encodeA(a), encodeB(b), encodeC(c)|]);
  let tuple4 = (encodeA, encodeB, encodeC, encodeD, (a, b, c, d)) =>
    jsonArray([|encodeA(a), encodeB(b), encodeC(c), encodeD(d)|]);

  let ior = (encodeA, encodeB) =>
    Ior.fold(encodeA >> List.pure, encodeB >> List.pure, (a, b) =>
      [a |> encodeA, b |> encodeB]
    );

  external stringArray: array(string) => Js.Json.t = "%identity";
  external numberArray: array(float) => Js.Json.t = "%identity";
  external boolArray: array(bool) => Js.Json.t = "%identity";

  let encodeAny = x =>
    x
    |> Js.Json.stringifyAny
    |> Option.flatMap(str =>
         try(Some(str |> Js.Json.parseExn)) {
         | _exn => None
         }
       )
    |> Option.getOrElse(Js.Json.null);
};

let getEmpty = Js.Dict.empty >> Encode.dict;
