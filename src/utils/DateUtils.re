/* Date conversion utility */
let jsFloatToISOString = (jsDate: float): string => {
  let dateObj = Js.Date.fromFloat(jsDate);
  Js.Date.toISOString(dateObj);
};
