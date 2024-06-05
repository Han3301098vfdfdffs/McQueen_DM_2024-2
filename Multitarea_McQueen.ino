#include <ESP32Servo.h>

const int ENApin = 23;
const int IN1pin = 22;
const int IN2pin = 21;
const int ENBpin = 5;

int IN1 = 0;
int IN2 = 0;
int ENA = 0;
int ENB = 0;
int ServoValue = 90;

TaskHandle_t Tarea1;  // Tarea1 Control Motor DC
TaskHandle_t Tarea3;  // Tarea3 Control Servo
Servo servoMotor;

void setup() {
  Serial.begin(115200);
  pinMode(IN1pin, OUTPUT);
  pinMode(IN2pin, OUTPUT);
  pinMode(ENApin, OUTPUT);
  pinMode(ENBpin, OUTPUT);

  xTaskCreatePinnedToCore(loop3, "Tarea_3", 1000, NULL, 1, &Tarea3, 1);
  xTaskCreatePinnedToCore(loop1, "Tarea_1", 1000, NULL, 1, &Tarea1, 0);
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    parseInput(input);
  }
}

void parseInput(String input) {
  char* token = strtok(const_cast<char*>(input.c_str()), ":"); 

  if (token != NULL) {
    IN1 = atoi(token);  
    token = strtok(NULL, ":");  

    if (token != NULL) {
      IN2 = atoi(token);
      token = strtok(NULL, ":");

      if (token != NULL) {
        ENA = atoi(token);
        token = strtok(NULL, ":");

        if (token != NULL) {
          ENB = atoi(token);
          token = strtok(NULL, ":");

          if (token != NULL) {
            ServoValue = atoi(token);
            token = strtok(NULL, ":");
          }
        }
      }
    }
  }
  updatePins();
}

void updatePins() {
  servoMotor.attach(15);
}

void loop1(void *parameter) {  
  while (true) {
    digitalWrite(IN1pin, IN1);
    digitalWrite(IN2pin, IN2);
    analogWrite(ENApin, ENA);
    analogWrite(ENBpin, ENB);  // Corregido el pin aquí
    delay(10);
  }
}

void loop3(void *parameter) {  
  while (true) {
    servoMotor.write(ServoValue);   
    delay(10);
  }
}
