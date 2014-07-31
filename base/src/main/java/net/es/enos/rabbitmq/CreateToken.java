/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.rabbitmq;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.QueueingConsumer;
import net.es.enos.kernel.exec.KernelThread;

import java.util.UUID;

/**
 * Created by davidhua on 7/3/14.
 */

/**
 * Creates a token request for the producer, which will be processed with processTokenRequest.
 * This token is then stored in "token."
 */

public class CreateToken {

	BrokerInfo info;
	String token;

	public CreateToken(BrokerInfo info, Channel tokenChannel, String listenerID) throws Exception{
		// Info on data needed to create a connection
		this.info = info;

		// Create random UUID for producer's temporary queue
		String uuid = UUID.randomUUID().toString();
		// Declare this temporary queue and start listening (exclusive queue).
		tokenChannel.queueDeclare(uuid, false, true, true, null);
		QueueingConsumer consumer = new QueueingConsumer(tokenChannel);

		// Send TOKEN_REQUEST with current username.
		String message = "TOKEN_REQUEST" + ":" +  uuid + ":" + KernelThread.currentKernelThread().getUser().getName();

		tokenChannel.basicPublish("", listenerID, null, message.getBytes());
		// Start consuming to receive token.
		tokenChannel.basicConsume(uuid, true, "tokenRequest", false, false, null, consumer);
		QueueingConsumer.Delivery delivery = consumer.nextDelivery();

		// When token is received, store in "token."
		token = new String(delivery.getBody());
		// Delete temporary queue
		tokenChannel.queueDelete(uuid);
	}

	public String getToken() {
		return token;
	}

	public void setToken(String token) {
		this.token = token;
	}
}