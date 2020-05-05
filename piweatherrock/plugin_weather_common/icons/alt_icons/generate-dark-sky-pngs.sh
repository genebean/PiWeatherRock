# Convert icons downloaded from https://erikflowers.github.io/weather-icons
# from svg to png. The icons converted are based on the API mapping provided at
# https://erikflowers.github.io/weather-icons/api-list.html

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 [path to folder of svg weather icons]"
  echo "Ex:    $0 ~/Downloads/weather-icons-master/svg"
  exit 1
else
  svg_folder=$1
fi

[ ! -d "64" ] && mkdir 64
[ ! -d "256" ] && mkdir 256

function convert() {
  svg_folder=$1
  input=$3
  output=$2

  output_icon=$(echo $output |sed -E 's/wi-forecast-io-(.+):/\1/')
  cairosvg "${svg_folder}/wi-${input}.svg" -o 64/${output_icon}.png -W 64 -H 64
  cairosvg "${svg_folder}/wi-${input}.svg" -o 256/${output_icon}.png -W 256 -H 256
}

convert $svg_folder wi-forecast-io-clear-day: day-sunny
convert $svg_folder wi-forecast-io-clear-night: night-clear
convert $svg_folder wi-forecast-io-rain: rain
convert $svg_folder wi-forecast-io-snow: snow
convert $svg_folder wi-forecast-io-sleet: sleet
convert $svg_folder wi-forecast-io-wind: strong-wind
convert $svg_folder wi-forecast-io-fog: fog
convert $svg_folder wi-forecast-io-cloudy: cloudy
convert $svg_folder wi-forecast-io-partly-cloudy-day: day-cloudy
convert $svg_folder wi-forecast-io-partly-cloudy-night: night-cloudy
convert $svg_folder wi-forecast-io-hail: hail
convert $svg_folder wi-forecast-io-thunderstorm: thunderstorm
convert $svg_folder wi-forecast-io-tornado: tornado

