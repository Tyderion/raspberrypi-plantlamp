<?php
$config = parse_ini_file("config.ini",true);
//print_r($_POST);
//print "<br />";
//print_r($config);
if (isset($_POST["weekend_on"]))
{
  $secret = $_POST["secret"];
  $secret_confirmation = $_POST["secret_confirmation"];
  $secret_change = $_POST["secret_change"];
  if ( md5($secret) == $config["Others"]["secret"] )
  {
$string = "[Weekend]
turn_on = {$_POST["weekend_on"]}
turn_off = {$_POST["weekend_off"]}

[Weekday]
turn_on = {$_POST["weekday_on"]}
turn_off = {$_POST["weekday_off"]}

[Others]
status = {$config["Others"]["status"]}
mode = \"{$_POST["mode"]}\"";
  if ($secret_confirmation != "" && $secret_confirmation == $secret_change)
  {
    $string = $string . "\nsecret = " . md5($secret_confirmation);
  }
  else
  {
    $string = $string . "\nsecret = " . md5($secret);
  }
  $fp = FOPEN("config.ini", "w");
  FWRITE($fp, $string);
  FCLOSE($fp);
  }
}
$config = parse_ini_file("config.ini",true);
//print "<br />";
//print_r($config);
print <<< EOT
<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Test successful</title>
</head>
<body>
  <form action="index.php" method="post" target="_self">
  Weekend<br />
   <label for="weekend_on"> On </label>: <input type="text" name="weekend_on" value={$config["Weekend"]["turn_on"]}> </input> <br />
   <label for="weekend_off"> Off </label>: <input type="text" name="weekend_off" value={$config["Weekend"]["turn_off"]}> </input> <br />
  Weekday<br />
   <label for="weekday_on"> On </label>: <input type="text" name="weekday_on" value={$config["Weekday"]["turn_on"]}> </input> <br />
   <label for="weekday_off"> Off </label>: <input type="text" name="weekday_off" value={$config["Weekday"]["turn_off"]}> </input> <br />
   <label for="mode"> Mode </label>
  <select name="mode" size="3">
EOT;

 switch ($config["Others"]["mode"]) {
    case "Automatic":
        print <<< EOT
        <option selected> Automatic </option>
        <option > Web </option>
        <option > On </option>
        <option > Off </option>
EOT;
        break;
    case "On":
        print <<< EOT
        <option > Automatic </option>
        <option > Web </option>
        <option selected> On </option>
        <option > Off </option>
EOT;
        break;
    case "Off":
        print <<< EOT
        <option > Automatic </option>
        <option > Web </option>
        <option > On </option>
        <option selected> Off </option>
EOT;
        break;
    case "Web":
        print <<< EOT
        <option > Automatic </option>
        <option selected> Web </option>
        <option > On </option>
        <option > Off </option>
EOT;

};
print <<< EOT
    </select><br />
  <label for="secret"> Secret </label> <input type="password" name="secret" /> <br />

  <label for="secret_change"> Change Secret </label> <input type="password" name="secret_change" /> <br />
  <label for="secret_confirmation"> Confirmation </label> <input type="password" name="secret_confirmation" /> <br />
  <input type="submit" value="Submit" />
</form>
<div id="log">
EOT;
$lastLines = `tail -n 10 plant.log`;
print $lastLines;
print "</div>";
?>
</body>
</html>

