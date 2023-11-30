#define safe_led 9
#define hazard_led 10
#define hazard_buzzer 8
int incomingByte = 0; // for incoming serial data
int safe_cond(){
  for (int z=0; z>= 0; z++){
  digitalWrite(safe_led, HIGH);
  digitalWrite(hazard_led, LOW);
  //digitalWrite(hazard_buzzer, LOW);
  noTone(hazard_buzzer);
  incomingByte = Serial.read()-'0';
  if (incomingByte == 1)hazard_cond();
  delay (200);}
}
int hazard_cond(){
  for (int k=0; k>=0; k++){
    digitalWrite(hazard_led, HIGH);
    digitalWrite(safe_led, LOW);
    if (k%2 == 1){
      tone(hazard_buzzer,1000);}
    else if (k%2 == 0){
      tone(hazard_buzzer,1200);}
    Serial.println(k);
    incomingByte = Serial.read()-'0';
    if (incomingByte == 0)safe_cond();
    delay(300);}
}

void setup() {
  Serial.begin(9600); // opens serial port, sets data rate to 9600 bps
  Serial.println("Start!");
  pinMode(safe_led, OUTPUT);
  pinMode(hazard_led, OUTPUT);
  pinMode(hazard_buzzer, OUTPUT);

}

void loop() {
  // send data only when you receive data:
  if (Serial.available() > 0) {
    // read the incoming byte:
    incomingByte = Serial.read()-'0';
    if (incomingByte == 1){
      Serial.println("Hazard condition.");
      hazard_cond();
    }
    else if (incomingByte == 0) {
      Serial.println("Safe condition.");
      safe_cond();
    }
  }
}