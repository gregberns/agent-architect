let divInt: (int, int) => float =
  (num, denom) => (num |> Int.toFloat) /. (denom |> Int.toFloat);
let sum: array(int) => int = arr => arr |> Array.foldLeft((+), 0);
let len: array(int) => int = Array.length;
let avg: array(int) => float = arr => divInt(sum(arr), len(arr));
