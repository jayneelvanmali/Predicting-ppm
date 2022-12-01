
#include <ESP8266WiFi.h>
#include <SPI.h>
#include <DHT.h>
#include "MQ135.h"
#define DHTTYPE DHT11     // DHT 11
#define DHTPIN 2     // DHT 11

float air_quality;
DHT dht(DHTPIN, DHTTYPE);


#define SECRET_SSID "Prashik"    // replace MySSID with your WiFi network name
#define SECRET_PASS "pratik66"  // replace MyPassword with your WiFi password

#define SECRET_CH_ID 1170558      // replace 0000000 with your channel number
#define SECRET_WRITE_APIKEY "1FION5VGJZ0EK2NS"   // replace XYZ with your channel write API Key

#include <ThingSpeak.h> // always include thingspeak header file after other header files and custom macros

char ssid[] = SECRET_SSID;   // your network SSID (name) 
char pass[] = SECRET_PASS;   // your network password
int keyIndex = 0;            // your network key Index number (needed only for WEP)
WiFiClient  client;

unsigned long myChannelNumber = SECRET_CH_ID;
const char * myWriteAPIKey = SECRET_WRITE_APIKEY;



void setup() {
  Serial.begin(115200);  // Initialize serial
  WiFi.mode(WIFI_STA); 
  ThingSpeak.begin(client);  // Initialize ThingSpeak
}

void loop() {

  // Connect or reconnect to WiFi
  if(WiFi.status() != WL_CONNECTED){
    Serial.print("Attempting to connect to SSID: ");
    Serial.println(SECRET_SSID);
    while(WiFi.status() != WL_CONNECTED){
      WiFi.begin(ssid, pass);  // Connect to WPA/WPA2 network. Change this line if using open or WEP network
      Serial.print(".");
      delay(5000);     
    } 
    Serial.println("\nConnected.");
  }
  float air_qualitycorrected;
  float hum = dht.readHumidity();
  float temp = dht.readTemperature(); // or dht.readTemperature(true) for Fahrenheit
  if (isnan(hum) || isnan(temp)) {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }
  delay(2000);
  MQ135 gasSensor = MQ135(A0);
  air_qualitycorrected = gasSensor.getCorrectedPPM(temp,hum);
  //Serial.println("Air Quality corrected:"+String(air_qualitycorrected));
  //air_quality = gasSensor.getPPM();
  //Serial.println("Air Quality:"+String(air_quality));

  //float r = gasSensor.getResistance();
   //Serial.println("Resistance:"+String(r));

   //float rzero = gasSensor.getCorrectedRZero(temp,hum);
   //Serial.println("Rzero:"+String(rzero));


    // set the fields with the values

  ThingSpeak.setField(1, air_qualitycorrected);
  ThingSpeak.setField(2, temp);
  ThingSpeak.setField(3, hum);

  
  // write to the ThingSpeak channel
  int x = ThingSpeak.writeFields(myChannelNumber, myWriteAPIKey);
  if(x == 200){
  Serial.println("============================New Data==================================");

 Serial.print(air_qualitycorrected);
 Serial.println(" PPM.Send to Thingspeak.");
 Serial.print("Temperature: ");
 Serial.print(temp);
 Serial.println("°C Send to Thingspeak.");
 Serial.print("Humidity: ");
 Serial.print(hum);
 Serial.println("% Send to Thingspeak.");

 int comp1=int(air_qualitycorrected);
 if(comp1>1000){
 Serial.println("Danger! Move to Fresh Air");
 }

 int comp2=int(temp);
 int comp3=int(hum);
 if(comp2>30 || comp3>80){
 Serial.println("High Temperature and Humidity! please try to lower home temperature");
         }
  }
  else{
    Serial.println("Problem updating channel. HTTP error code " + String(x));
  }
  
  
  delay(20000); // Wait 20 seconds to update the channel again
}
