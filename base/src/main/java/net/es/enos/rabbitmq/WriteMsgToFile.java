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
import java.text.SimpleDateFormat;
import java.util.Calendar;

/**
 * Created by davidhua on 7/8/14.
 */

/**
 * Writes each message received to a file with a time stamp.
 */

public class WriteMsgToFile {
	String userFile = "";
	String messageFile = "/Messages.txt";

	public WriteMsgToFile(String user) {
		userFile = user;
	}

	public void writeMsg(String message, String user) throws IOException {
		Calendar cal = Calendar.getInstance();
		SimpleDateFormat sdf = new SimpleDateFormat("HH:mm:ss");

		File msgFile = new File(this.userFile + messageFile);

		if (!msgFile.exists()) {
			if (!msgFile.createNewFile()) {
				throw new RuntimeException("Cannot create " + this.userFile);
			}
		}

		FileWriter fw = new FileWriter(msgFile.getAbsoluteFile(), true);
		BufferedWriter bw = new BufferedWriter(fw);
		String write = sdf.format(cal.getTime()) + " : [x] Received \"" + message + "\" from " + user + "\n";
		bw.write(write);
		bw.close();

	}
}