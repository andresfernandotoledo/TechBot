package com.techbot.app;

import android.Manifest;
import android.annotation.SuppressLint;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;
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

import com.chaquo.python.Python;
import com.chaquo.python.PyObject;
import com.chaquo.python.android.AndroidPlatform;
import com.techbot.bridge.TechBotBridge;

@SuppressLint("SetJavaScriptEnabled")
public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private SwipeRefreshLayout swipeRefresh;
    private ProgressBar progressBar;
    private LinearLayout topBar;
    private EditText urlInput;
    private ImageButton goBtn, settingsBtn, refreshBtn;
    private SharedPreferences prefs;
    private static final int CAMERA_PERM_CODE = 100;
    private static final int LOCATION_PERM_CODE = 101;
    private static final String TAG = "TechBot";
    private boolean serverStarted = false;
    private Handler mainHandler = new Handler(Looper.getMainLooper());

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("techbot", MODE_PRIVATE);

        topBar = findViewById(R.id.topBar);
        urlInput = findViewById(R.id.urlInput);
        goBtn = findViewById(R.id.goBtn);
        settingsBtn = findViewById(R.id.settingsBtn);
        refreshBtn = findViewById(R.id.refreshBtn);
        progressBar = findViewById(R.id.progressBar);
        swipeRefresh = findViewById(R.id.swipeRefresh);
        webView = findViewById(R.id.webView);

        // Inicializar bridge nativo
        TechBotBridge.init(this);

        // Permisos
        requestPermissions();

        // Config WebView
        setupWebView();

        // Iniciar servidor Flask embebido
        startEmbeddedServer();
    }

    private void requestPermissions() {
        String[] needed = {};
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            needed = new String[]{Manifest.permission.CAMERA};
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                    != PackageManager.PERMISSION_GRANTED) {
                needed = new String[]{Manifest.permission.CAMERA, Manifest.permission.ACCESS_FINE_LOCATION};
            }
        }
        if (needed.length > 0) {
            ActivityCompat.requestPermissions(this, needed, CAMERA_PERM_CODE);
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void setupWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        settings.setUserAgentString(settings.getUserAgentString() + " TechBot-Android");
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setDatabaseEnabled(true);

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
            public void onPageFinished(WebView view, String url) {
                super.onPageFinished(view, url);
                swipeRefresh.setRefreshing(false);
            }

            @Override
            public void onReceivedError(WebView view, int errorCode, String description, String failingUrl) {
                Log.e(TAG, "WebView error: " + errorCode + " " + description);
                if (!serverStarted) {
                    // Server not ready yet, show loading message
                    view.loadDataWithBaseURL(null,
                            "<html><body style='background:#1a1a2e;color:#e0e0e0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;font-family:sans-serif'>" +
                                    "<div style='text-align:center'><h2>🚀 TechBot</h2>" +
                                    "<p style='color:#888'>Iniciando servidor local...</p>" +
                                    "<div style='width:40px;height:40px;border:3px solid #00d4ff;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite;margin:20px auto'></div>" +
                                    "<style>@keyframes spin{to{transform:rotate(360deg)}}</style>" +
                                    "<p style='color:#555;font-size:12px' id='status'>Conectando...</p>" +
                                    "<script>" +
                                    "var attempts=0;" +
                                    "function check(){" +
                                    "  fetch('/api/status').then(r=>r.json()).then(d=>{" +
                                    "    document.getElementById('status').textContent='✅ Servidor listo';" +
                                    "    setTimeout(()=>location.reload(),500);" +
                                    "  }).catch(()=>{" +
                                    "    attempts++;" +
                                    "    document.getElementById('status').textContent='⏳ Intento '+attempts+'...';" +
                                    "    setTimeout(check,1000);" +
                                    "  })" +
                                    "}" +
                                    "setTimeout(check,2000);" +
                                    "</script></div></body></html>",
                            "text/html", "UTF-8", null);
                }
            }
        });

        swipeRefresh.setOnRefreshListener(() -> webView.reload());

        // Botones
        urlInput.setOnEditorActionListener((v, actionId, event) -> {
            loadUrl();
            return true;
        });
        if (goBtn != null) goBtn.setOnClickListener(v -> loadUrl());
        if (refreshBtn != null) refreshBtn.setOnClickListener(v -> webView.reload());
        if (settingsBtn != null) settingsBtn.setOnClickListener(v -> showSettings());

        // Cargar ultima URL o localhost
        String savedUrl = prefs.getString("server_url", "http://127.0.0.1:5000");
        urlInput.setText(savedUrl);
    }

    private void startEmbeddedServer() {
        new Thread(() -> {
            try {
                Log.d(TAG, "Iniciando Python (Chaquopy)...");

                // Inicializar Chaquopy
                if (!Python.isStarted()) {
                    Python.start(new AndroidPlatform(this));
                }

                Python py = Python.getInstance();
                PyObject serverModule = py.getModule("server");

                Log.d(TAG, "Llamando server.start()...");
                serverModule.callAttr("start", 5000);

            } catch (Exception e) {
                Log.e(TAG, "Error iniciando servidor Python", e);
                mainHandler.post(() -> {
                    Toast.makeText(this,
                            "Error iniciando servidor: " + e.getMessage(),
                            Toast.LENGTH_LONG).show();
                    // Fallback: cargar URL externa
                    webView.loadUrl(urlInput.getText().toString());
                });
            }
        }, "techbot-server").start();

        // Esperar a que el servidor esté listo y cargar WebView
        new Thread(() -> {
            int attempts = 0;
            while (attempts < 30) {
                try {
                    java.net.URL url = new java.net.URL("http://127.0.0.1:5000/api/status");
                    java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                    conn.setConnectTimeout(1000);
                    conn.setReadTimeout(500);
                    int code = conn.getResponseCode();
                    conn.disconnect();
                    if (code == 200) {
                        serverStarted = true;
                        Log.d(TAG, "Servidor listo! Cargando WebView...");
                        mainHandler.post(() -> {
                            webView.loadUrl("http://127.0.0.1:5000");
                        });
                        return;
                    }
                } catch (Exception e) {
                    // Server not ready yet
                }
                attempts++;
                try { Thread.sleep(500); } catch (InterruptedException ie) { return; }
            }
            // Timeout - cargar URL manual
            Log.e(TAG, "Servidor no respondió después de 15s");
            mainHandler.post(() -> {
                Toast.makeText(this, "Tiempo de espera agotado. Verificá la URL.", Toast.LENGTH_LONG).show();
                webView.loadUrl(urlInput.getText().toString());
            });
        }, "techbot-wait").start();
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
        builder.setTitle("⚙️ TechBot");
        builder.setItems(new String[]{
                "Cambiar URL del servidor",
                "Reiniciar servidor",
                "Compartir app",
                "Acerca de"
        }, (dialog, which) -> {
            switch (which) {
                case 0:
                    showUrlDialog();
                    break;
                case 1:
                    webView.loadUrl("about:blank");
                    webView.loadUrl("http://127.0.0.1:5000");
                    Toast.makeText(this, "Reconectando...", Toast.LENGTH_SHORT).show();
                    break;
                case 2:
                    Intent share = new Intent(Intent.ACTION_SEND);
                    share.setType("text/plain");
                    share.putExtra(Intent.EXTRA_TEXT,
                            "TechBot - Asistente técnico para redes, CCTV y sistemas\n" +
                                    "Descargá el servidor: github.com/techbot-app");
                    startActivity(Intent.createChooser(share, "Compartir"));
                    break;
                case 3:
                    new AlertDialog.Builder(this)
                            .setTitle("TechBot v1.0")
                            .setMessage("Asistente técnico multiplataforma para redes, CCTV y sistemas.\n\n" +
                                    "• Escáner de red (TCP/UDP)\n" +
                                    "• DNS, SSL, WHOIS, NTP\n" +
                                    "• SNMP, WiFi, DHCP\n" +
                                    "• Speedtest, UPS, IPAM\n" +
                                    "• Topología interactiva\n" +
                                    "• 92 API endpoints\n\n" +
                                    "Python embebido vía Chaquopy")
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
