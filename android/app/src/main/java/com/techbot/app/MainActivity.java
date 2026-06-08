package com.techbot.app;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

@SuppressLint("SetJavaScriptEnabled")
public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private SwipeRefreshLayout swipeRefresh;
    private ProgressBar progressBar;
    private LinearLayout topBar;
    private EditText urlInput;
    private ImageButton goBtn, settingsBtn;
    private SharedPreferences prefs;
    private static final int CAMERA_PERM_CODE = 100;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("techbot", MODE_PRIVATE);

        topBar = findViewById(R.id.topBar);
        urlInput = findViewById(R.id.urlInput);
        goBtn = findViewById(R.id.goBtn);
        settingsBtn = findViewById(R.id.settingsBtn);
        progressBar = findViewById(R.id.progressBar);
        swipeRefresh = findViewById(R.id.swipeRefresh);
        webView = findViewById(R.id.webView);

        // Config WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " TechBot-Android");

        // Camera for QR
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA}, CAMERA_PERM_CODE);
        }

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                request.grant(request.getResources());
            }

            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                progressBar.setProgress(newProgress);
                progressBar.setVisibility(newProgress < 100 ? View.VISIBLE : View.GONE);
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                String url = request.getUrl().toString();
                if (url.startsWith("http://") || url.startsWith("https://")) {
                    view.loadUrl(url);
                }
                return false;
            }
        });

        // Pull to refresh
        swipeRefresh.setOnRefreshListener(() -> webView.reload());

        // Navigation
        goBtn.setOnClickListener(v -> loadUrl());
        urlInput.setOnEditorActionListener((v, actionId, event) -> {
            loadUrl();
            return true;
        });
        settingsBtn.setOnClickListener(v -> showSettings());

        // Load last URL or default
        String savedUrl = prefs.getString("server_url", "http://localhost:5000");
        urlInput.setText(savedUrl);
        webView.loadUrl(savedUrl);
    }

    private void loadUrl() {
        String url = urlInput.getText().toString().trim();
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        prefs.edit().putString("server_url", url).apply();
        webView.loadUrl(url);
    }

    private void showSettings() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("Configuración");
        builder.setItems(new String[]{
                "Cambiar URL del servidor",
                "Compartir app",
                "Acerca de"
        }, (dialog, which) -> {
            switch (which) {
                case 0:
                    showUrlDialog();
                    break;
                case 1:
                    Intent share = new Intent(Intent.ACTION_SEND);
                    share.setType("text/plain");
                    share.putExtra(Intent.EXTRA_TEXT,
                            "TechBot - Asistente técnico\n" + urlInput.getText().toString());
                    startActivity(Intent.createChooser(share, "Compartir"));
                    break;
                case 2:
                    new AlertDialog.Builder(this)
                            .setTitle("TechBot v1.0")
                            .setMessage("Asistente técnico para redes, CCTV y sistemas.\n\n" +
                                    "Corre el servidor Flask en tu PC o Termux y conectate desde acá.")
                            .setPositiveButton("OK", null)
                            .show();
                    break;
            }
        });
        builder.show();
    }

    private void showUrlDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("URL del servidor");
        View view = getLayoutInflater().inflate(android.R.layout.simple_list_item_1, null);
        EditText input = new EditText(this);
        input.setText(urlInput.getText());
        input.setSelection(input.getText().length());
        builder.setView(input);
        builder.setPositiveButton("Conectar", (d, w) -> {
            String url = input.getText().toString().trim();
            if (!url.isEmpty()) {
                urlInput.setText(url);
                loadUrl();
            }
        });
        builder.setNegativeButton("Cancelar", null);
        builder.show();
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && webView.canGoBack()) {
            webView.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
