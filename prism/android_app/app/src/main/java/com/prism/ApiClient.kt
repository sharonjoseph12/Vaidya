package com.prism

import java.io.IOException

class ApiClient {
    fun submitScan(sessionData: Map<String, Any>): Boolean {
        // Use Retrofit to submit multipart data to FastAPI backend
        // If offline, gracefully degrade and run PRISMModule locally
        return true
    }
}
