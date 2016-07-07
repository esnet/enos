/*
 * ESnet Network Operating System (ENOS) Copyright (c) 2016, The Regents
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
 *
 */
package net.es.enos.services;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;

/**
 *
 * @author hacksaw
 */
@ApiModel(value="Error", description="Error structure for REST interface.")
public class Error {
    private String error;               // short description
    private String error_description;   // longer description, human-readable.
    private String error_uri;           // URI to a detailed error description on the API developer website.

    public Error(String error, String error_description, String error_uri) {
        this.error = error;
        this.error_description = error_description;
        this.error_uri = error_uri;
    }

    protected Error(Builder builder) {
        this.error = builder.error;
        this.error_description = builder.error_description;
        this.error_uri = builder.error_uri;
    }

    /**
     * @return the error
     */
    @ApiModelProperty(value = "Short description of error")
    public String getError() {
        return error;
    }

    /**
     * @param error the error to set
     */
    public void setError(String error) {
        this.error = error;
    }

    /**
     * @return the error_description
     */
    @ApiModelProperty(value = "Longer human-readable description of error.")
    public String getError_description() {
        return error_description;
    }

    /**
     * @param error_description the error_description to set
     */
    public void setError_description(String error_description) {
        this.error_description = error_description;
    }

    /**
     * @return the error_uri
     */
    @ApiModelProperty(value = "URI to a detailed error description on the API developer website.")
    public String getError_uri() {
        return error_uri;
    }

    /**
     * @param error_uri the error_uri to set
     */
    public void setError_uri(String error_uri) {
        this.error_uri = error_uri;
    }

    public static class Builder {
    private String error;               // short description
    private String error_description;   // longer description, human-readable.
    private String error_uri;           // URI to a detailed error description on the API developer website.

        public Builder() {
        }

        public Builder withError(String error) {
            this.error = error;
            return this;
        }

        public Builder withErrorDescription(String error_description) {
            this.error_description = error_description;
            return this;
        }


        public Builder withErrorUri(String error_uri) {
            this.error_uri = error_uri;
            return this;
        }


        public Error build() { return new Error(this); }
    }
}
