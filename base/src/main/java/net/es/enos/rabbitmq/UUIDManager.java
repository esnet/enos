/*
 * Copyright (c) 2014, Regents of the University of California  All rights reserved.
 * Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
 * 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package net.es.enos.rabbitmq;

import java.io.*;
import java.util.UUID;

/**
 * Created by davidhua on 7/2/14.
 */

/**
 * Checks to see if a UUID file exists (for the consumer queue), and if not creates one. If it does, read from it and
 * use as the queue name.
 */

public class UUIDManager {
	String queueName = " ";
	String queueFile = " ";
	String queueFileName = "/queueNameFile";

	public UUIDManager(String queue) {
		queueFile = queue;
	}

	public String checkUUID() throws IOException {
		File queueFile = new File(this.queueFile + queueFileName);

		if (!queueFile.exists()) {
			// File does not exist yet, create it.
			if (!queueFile.createNewFile()) {
				// File could not be created.
				throw new RuntimeException("Cannot create " + this.queueFile);
			}
		}
		// If file is empty, create random UUID and write in file.
		// Else, read first line from file. Return UUID.
		if (queueFile.length() == 0) {
			String uuid = UUID.randomUUID().toString();

			FileWriter fw = new FileWriter(queueFile.getAbsoluteFile());
			BufferedWriter bw = new BufferedWriter(fw);
			bw.write(uuid);
			queueName = uuid;
			bw.close();
		} else {
			FileReader fr = new FileReader(queueFile);
			LineNumberReader ln = new LineNumberReader(fr);
			queueName = ln.readLine();
		}
		return queueName;
	}
}