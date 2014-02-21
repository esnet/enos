package net.es.enos.kernel.exec;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Created by lomax on 2/11/14.
 */


public class TeeOutputStream  extends OutputStream {
        private InputStream in = null;
        private int[] buffer;
        private int writeIndex = -1;
        private int readIndex = -1;

        public class TeeOutInputStream extends InputStream {
            private TeeOutputStream out = null;
            protected TeeOutInputStream (TeeOutputStream out) {
                this.out = out;
            }
            public int read() {
                return this.waitUntilAvail();
            }

            private synchronized int waitUntilAvail() {
                while (true) {
                    if (this.out.checkReadAvailable()) {
                        return this.out.get();
                    } else {
                        try {
                            this.wait();
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                }
            }
        }

        public TeeOutputStream (int size) {
            this.buffer = new int[size];
        }

        public InputStream getInputStream () {
            return this.in;
        }
        public void write(int c) throws IOException {
            this.push(c);
        }

        public boolean checkReadAvailable () {
            if (this.readIndex != this.writeIndex) {
                return true;
            } else {
                return false;
            }
        }
        public synchronized int get() {
            if (++this.readIndex == (this.buffer.length -1)) {
                // Wrap around
                this.readIndex = 0;
            }
            return this.buffer[this.readIndex];
        }

        public synchronized void push(int c) {
            int i = this.writeIndex;
            // Wrap around if needed
            if (++i == (this.buffer.length -1)) {
                i = 0;
            }
            if (i == this.readIndex) {
                // Buffer is full. Silently drop
                return;
            }
            this.buffer[i] = c;
            this.writeIndex = i;
            // Notify read thread if any.
            this.notify();
        }
}



