package com.prism

import android.content.Context
import org.tensorflow.lite.Interpreter
import org.tensorflow.lite.gpu.CompatibilityList
import org.tensorflow.lite.gpu.GpuDelegate
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel
import java.io.FileInputStream

class PRISMModule(context: Context) {
    private var interpreter: Interpreter? = null
    private var gpuDelegate: GpuDelegate? = null

    init {
        val compatList = CompatibilityList()
        val options = Interpreter.Options().apply {
            if(compatList.isDelegateSupportedOnThisDevice) {
                gpuDelegate = GpuDelegate(compatList.bestOptionsForThisDevice)
                this.addDelegate(gpuDelegate)
            } else {
                this.setNumThreads(4)
            }
        }
        
        // Example loading logic - models provided by Person 1
        // val modelBuffer = loadModelFile(context, "fusion_model.tflite")
        // interpreter = Interpreter(modelBuffer, options)
    }

    private fun loadModelFile(context: Context, modelName: String): MappedByteBuffer {
        val fileDescriptor = context.assets.openFd(modelName)
        val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
        val fileChannel = inputStream.channel
        return fileChannel.map(FileChannel.MapMode.READ_ONLY, fileDescriptor.startOffset, fileDescriptor.declaredLength)
    }

    fun close() {
        interpreter?.close()
        gpuDelegate?.close()
    }
}
