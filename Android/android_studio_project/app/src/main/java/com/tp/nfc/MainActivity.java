package com.tp.nfc;

import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import android.widget.TextView;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

public class MainActivity extends AppCompatActivity {

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        // Initialize Python if not already initialized
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }

        TextView textView = findViewById(R.id.text_view);
        
        try {
            // Get Python instance
            Python py = Python.getInstance();
            
            // Import and run the main Python module
            PyObject module = py.getModule("main_kivymd");
            
            // For now, just show a simple message
            // The actual Kivy app would need more complex integration
            textView.setText("TP_NFC Android - Python Initialized Successfully!\n\nKivy app integration in progress...");
            
        } catch (Exception e) {
            textView.setText("Error initializing Python: " + e.getMessage());
            e.printStackTrace();
        }
    }
}