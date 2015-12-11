/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
 * of the University of California, through Lawrence Berkeley National
 * Laboratory (subject to receipt of any required approvals from the
 * U.S. Dept. of Energy).  All rights reserved.
 *
 * If you have questions about your rights to use or distribute this
 * software, please contact Berkeley Lab's Innovation & Partnerships
 * Office at IPO@lbl.gov.
 *
 * NOTICE.  This Software was developed under funding from the
 * U.S. Department of Energy and the U.S. Government consequently retains
 * certain rights. As such, the U.S. Government has been granted for
 * itself and others acting on its behalf a paid-up, nonexclusive,
 * irrevocable, worldwide license in the Software to reproduce,
 * distribute copies to the public, prepare derivative works, and perform
 * publicly and display publicly, and to permit other to do so.
 */
package net.es.enos.perfsonar;

import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

/**
 * Base class of esmond filter objects.
 * This basically encapsulates the query string and the encoding needed
 * to create it.
 * Created by bmah on 8/5/14.
 */
abstract public class EsmondFilter {

    /**
     * Helper class to construct query string
     */
    protected class QueryString {

        private String query = "";

        void add(String key, String value) {
            if (!query.isEmpty()) {
                query += "&";
            }
            try {
                query += URLEncoder.encode(key, "UTF-8");
                query += "=";
                query += URLEncoder.encode(value, "UTF-8");
            }
            catch (UnsupportedEncodingException e) {
                throw new RuntimeException("barf");
            }
        }

        public String getQuery() {
            return query;
        }
    }

    abstract public String toUrlQueryString();
}
