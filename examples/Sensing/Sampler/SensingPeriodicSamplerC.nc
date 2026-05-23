/*
 * Copyright (c) 2007 Stanford University.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * - Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * - Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the
 *   distribution.
 * - Neither the name of the Stanford University nor the names of
 *   its contributors may be used to endorse or promote products derived
 *   from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL STANFORD
 * UNIVERSITY OR ITS CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * @author Kevin Klues <klueska@cs.stanford.edu>
 * @date July 24, 2007
 */

//#include "printf.h"
#include "SensingConstants.h"
#include "SensorSample.h"

module SensingPeriodicSamplerC {
  uses {
    interface Boot;
    interface Timer<TMilli> as SampleTimer;
    interface Leds;
    interface SplitControl as AMControl;
    interface AMPacket;
    interface Packet;
    interface AMSend as SampleSend;
    interface Read<uint16_t> as ReadTemp;
    interface Read<uint16_t> as ReadHumidity;
  }
}
implementation {
  message_t sample_msg;
  bool sendBusy;
  uint16_t temp_val;
  uint16_t hum_val;
  uint32_t count;

  event void Boot.booted() {
    sendBusy = FALSE;
    temp_val = 0;
    hum_val = 0;
    count = 0;
    call AMControl.start();
  }

  event void AMControl.startDone(error_t e) {
    if (e != SUCCESS)
      call AMControl.start();
    else
      call SampleTimer.startPeriodic(20000);
  }

  event void AMControl.stopDone(error_t e) {}

  event void SampleTimer.fired() {
    call Leds.led0Toggle();
    call ReadTemp.read();
  }

  event void ReadTemp.readDone(error_t e, uint16_t val) {
    if (e == SUCCESS) temp_val = val;
    call ReadHumidity.read();
  }

  event void ReadHumidity.readDone(error_t e, uint16_t val) {
    nx_sensor_sample_t* payload;
    if (e == SUCCESS) hum_val = val;
    if (!sendBusy) {
      payload = (nx_sensor_sample_t*)call SampleSend.getPayload(&sample_msg, sizeof(nx_sensor_sample_t));
      if (payload == NULL) return;
      payload->sample_num = count++;
      payload->temperature = temp_val;
      payload->humidity = hum_val;
      payload->photo_active = 0;
      payload->total_solar = 0;
      if (call SampleSend.send(BASE_STATION_ADDR, &sample_msg, sizeof(nx_sensor_sample_t)) == SUCCESS) {
        sendBusy = TRUE;
        call Leds.led2Toggle();
      }
    }
  }

  event void SampleSend.sendDone(message_t* msg, error_t e) {
    sendBusy = FALSE;
  }
}

