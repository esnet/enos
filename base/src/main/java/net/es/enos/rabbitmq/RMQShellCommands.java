package net.es.enos.rabbitmq;

import net.es.enos.api.TopologyFactory;
import net.es.enos.kernel.exec.KernelThread;
import net.es.enos.shell.annotations.ShellCommand;
import org.jgrapht.graph.DefaultListenableGraph;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.InputStream;
import java.io.OutputStream;
import java.io.PrintStream;
import java.util.UUID;


/**
 * Created by davidhua on 7/30/14.
 */

public class RMQShellCommands {

	@ShellCommand(name = "GET_TOPOLOGY",
			shortHelp = "Sends topology over RMQ",
			longHelp = "Sends topology over RMQ")
	public static void queueRequest(String[] args, InputStream in, OutputStream out, OutputStream err) throws Exception {
		String host = "summer1.es.net";
		String username = "david2";
		String password = "123";
		int port = 5671;
		boolean ssl = false;

		PrintStream o = new PrintStream(out);
		try {
			Logger logger = LoggerFactory.getLogger(RMQShellCommands.class);

			logger.info("GET_TOPOLOGY", args.length);

			String currentUser = KernelThread.currentKernelThread().getUser().getName().toString();
			String queueName = UUID.randomUUID().toString();
			String sendQueue = args[1];

			o.println(args);
			BrokerInfo info = new BrokerInfo(host, username, password, port, ssl);
			Publish thisPublish = new Publish(info, sendQueue);
			TopologyFactory topology = TopologyFactory.instance();
			DefaultListenableGraph topo = topology.retrieveTopology("localLayer2");
			thisPublish.Publish(topo);
		} catch (Exception e) {
			o.println("ERROR");
		}
	}
}
