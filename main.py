from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import datetime
import logging
import mysql.connector


port = 8181


class Serv(BaseHTTPRequestHandler):
    tempCelsius = None
    tempFareng = None
    tempFeelsLike = None
    windSpeed = None
    windDeg = None
    sunrise = None
    sunset = None
    lat = None
    lon = None

    def init(self, tempCelsius, tempFareng, tempFeelsLike, windSpeed, windDeg, sunrise, sunset):
        self.tempCelsius = tempCelsius
        self.tempFareng = (tempFareng*(9/5))+32
        self.tempFeelsLike = tempFeelsLike
        self.windSpeed = windSpeed
        self.windDeg = self.degToDirection(windDeg)
        self.sunrise = self.unixTimeToNormalTime(sunrise).strftime('%H:%M')
        self.sunset = self.unixTimeToNormalTime(sunset).strftime('%H:%M')

    def initLatLon(self, lat, lon):
        self.lat = lat
        self.lon = lon

    def unixTimeToNormalTime(self, time):
        return datetime.datetime.fromtimestamp(time)

    def degToDirection(self, num):
        val = int((num / 22.5) + .5)
        arr = ["Север", "Северо-северо-восток", "Северо-восток", "Восток-северо-восток", "Восток", "Восток-юго-восток",
               "Юго-восток", "Юго-юго-восток", "Юг", "Юго-юго-запад", "Юго-запад", "Запад-юго-запад", "Запад",
               "Запад-северо-запад", "Северо-запад", "Северо-северо-запад"]
        return arr[(val % 16)]

    def printInfo(self, typedata, path, db, logger, N=0):

        query = "insert into weather (time, route, data) values (%s, %s, %s)"

        timeNow = str(datetime.datetime.now().time())
        route = "localhost:" + str(port) + "/" + path
        self.wfile.write('<h3>'.encode())
        with db.cursor() as cursor:
            if typedata == 'tempCelsius':
                self.wfile.write('Temperature in celsius: '.encode())
                self.wfile.write(str(self.tempCelsius).encode())
                db_data = [(timeNow, route, str(self.tempCelsius))]
                cursor.executemany(query, db_data)
            elif typedata == 'tempFareng':
                self.wfile.write('Temperature in farengeits: '.encode())
                self.wfile.write(str(self.tempFareng).encode())
                db_data = [(timeNow, route, str(self.tempFareng))]
                cursor.executemany(query, db_data)
            elif typedata == 'tempFeelsLike':
                self.wfile.write('Feeling temperature: '.encode())
                self.wfile.write(str(self.tempFeelsLike).encode())
                db_data = [(timeNow, route, str(self.tempFeelsLike))]
                cursor.executemany(query, db_data)
            elif typedata == 'windSpeed':
                self.wfile.write('Wind speed: '.encode())
                self.wfile.write(str(self.windSpeed).encode())
                db_data = [(timeNow, route, str(self.windSpeed))]
                cursor.executemany(query, db_data)
            elif typedata == 'windDeg':
                self.wfile.write('Wind degree: '.encode())
                self.wfile.write(str(self.windDeg).encode())
                db_data = [(timeNow, route, str(self.windDeg))]
                cursor.executemany(query, db_data)
            elif typedata == 'sunrise':
                self.wfile.write('Sunrise: '.encode())
                self.wfile.write(str(self.sunrise).encode())
                db_data = [(timeNow, route, str(self.sunrise))]
                cursor.executemany(query, db_data)
            elif typedata == 'sunset':
                self.wfile.write('Sunset: '.encode())
                self.wfile.write(str(self.sunset).encode())
                db_data = [(timeNow, route, str(self.sunset))]
                cursor.executemany(query, db_data)
            elif typedata == 'getLast':
                self.printLast(db, N)
            else:
                logger.error("Wrong path")
                exit(1)
            self.wfile.write('<h3>'.encode())


    def printLast(self, db, N):
        with db.cursor() as cursor:
            get_last_query = "select route, data from weather order by id desc limit " + str(N)
            cursor.execute(get_last_query)
            for row in cursor.fetchall():
                self.wfile.write(str(row).encode())
                self.wfile.write('<br />'.encode())

    def printMainPage(self):
        self.wfile.write('<h3>'.encode())
        self.wfile.write('Routes:<br />'.encode())
        self.wfile.write('1)localhost:port/lat/lon/tempCelsius - temperature in celsius<br />'.encode())
        self.wfile.write('2)localhost:port/lat/lon/tempFareng - temperature in farengeits<br />'.encode())
        self.wfile.write('3)localhost:port/lat/lon/tempFeelsLike - Feeling temperature<br />'.encode())
        self.wfile.write('4)localhost:port/lat/lon/windSpeed - wind speed<br />'.encode())
        self.wfile.write('5)localhost:port/lat/lon/windDeg - wind degree<br />'.encode())
        self.wfile.write('6)localhost:port/lat/lon/sunrise - sunrise time<br />'.encode())
        self.wfile.write('7)localhost:port/lat/lon/sunset - sunset time<br />'.encode())
        self.wfile.write('8)localhost:port/getlast/N - get last N routes<br />'.encode())
        self.wfile.write('<h3>'.encode())

    def checkLatLon(self, lat, lon, logger):
        if float(lat) > 90-0.0000001 or float(lat) < 0-0.0000001:
            logger.error("latitude must be <= 90 and >= 0")
            exit(1)
        elif float(lon) > 180-0.0000001 or float(lon) < 0-0.0000001:
            logger.error("longitude must be <= 180 and >= 0")
            exit(1)



    def do_GET(self):
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.end_headers()
        logger = logging.getLogger("log.GET")

        try:
            with mysql.connector.connect(host="localhost",
                                         user="anton",
                                         password="qwerty123",
                                         database="weather",
                                         port="3307") as connection:

                localpath = self.path[1:]
                logger.info("go to localhost:%d/%s address" % (port, localpath))
                if localpath == "":
                    self.printMainPage()
                else:
                    splitpath = localpath.split("/")

                    if len(splitpath) == 2 and splitpath[1].isdigit() and splitpath[0].isalpha():
                        self.printInfo(splitpath[0], localpath, connection, logger, splitpath[1])
                    elif len(splitpath)==3 and splitpath[0].isdigit() and splitpath[1].isdigit() and splitpath[2].isalpha():
                        self.checkLatLon(splitpath[0], splitpath[1], logger)
                        self.initLatLon(splitpath[0], splitpath[1])

                        link = "https://weather-proxy.freecodecamp.rocks/api/current?lat=" + self.lat + "&lon=" + self.lon
                        data = requests.get(link).json()

                        self.init(data['main']['temp'],
                                  data['main']['temp'],
                                  data['main']['feels_like'],
                                  data['wind']['speed'],
                                  data['wind']['deg'],
                                  data['sys']['sunrise'],
                                  data['sys']['sunset'])

                        self.printInfo(splitpath[2], localpath, connection, logger)
                        connection.commit()
                    else:
                        logger.error("Wrong path")
                        exit(1)
        except mysql.connector.Error as err:
            logger.error(err)
            exit(1)



def main():
    logger = logging.getLogger("log")
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler("logger.log")
    fh.setFormatter(logging.Formatter('%(asctime)s  %(levelname)s:  %(message)s'))
    logger.addHandler(fh)


    server = HTTPServer(("localhost", port), Serv)
    logger.info("Server start on port = %d" % port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

