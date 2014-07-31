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

import java.util.HashMap;
import java.util.UUID;

/**
 * Created by davidhua on 7/15/14.
 */

public class Box {

	HashMap<String, Queue> queueList;

	public Box() {
		this.queueList = new HashMap<String, Queue> ();
	}

	public Queue getQueue(String symLink) {
		return queueList.get(symLink);
	}

	public void registerQueue(Queue register) {
		queueList.put(register.getSymLink(), register);
	}

	public Queue createQueue(String symLink, Channel channel) throws Exception {
		String queueName = UUID.randomUUID().toString();
		channel.queueDeclare(queueName, false, false, true, null);
		QueueingConsumer consumer = new QueueingConsumer(channel);
		channel.basicConsume(queueName, true, symLink, false, false, null, consumer);

		return new Queue(queueName, symLink);
	}

	public String queryQueue(String sendQueue, String token, Channel channel, String symLink) throws Exception {

		// Create random UUID for producer's temporary queue
		String uuid = UUID.randomUUID().toString();
		// Declare this temporary queue and start listening (exclusive queue).
		channel.queueDeclare(uuid, false, true, true, null);
		QueueingConsumer consumer = new QueueingConsumer(channel);

		// Send TOKEN_REQUEST with curent username.
		String message = token + ":QUEUE_QUERY" + ":" +  uuid + ":" + KernelThread.currentKernelThread().getUser().getName() + ":" + symLink;

		channel.basicPublish("", sendQueue, null, message.getBytes());
		// Start consuming to receive token.
		channel.basicConsume(uuid, true, "tokenRequest", false, true, null, consumer);
		QueueingConsumer.Delivery delivery = consumer.nextDelivery();

		// When token is received, store in "token."
		String queueName = new String(delivery.getBody());
		// Delete temporary queue
		channel.queueDelete(uuid);

		return queueName;

	}

	public void responseQuery(String responseQueue, Channel channel, String symLink, String userName) throws Exception {
		Queue queryQueue = getQueue(symLink);
		if (queryQueue.hasPermission(userName)) {
			String message = queryQueue.getQueueName();
			channel.basicPublish("", responseQueue, null, message.getBytes());
		} else {
			throw new Exception("User does not have access to this queue");
		}
	}

}