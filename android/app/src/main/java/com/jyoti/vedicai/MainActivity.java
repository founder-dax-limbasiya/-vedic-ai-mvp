package com.jyoti.vedicai;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;
import java.io.InputStream;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.Collections;

public final class MainActivity extends Activity {
    private static final String LOCAL_HOST = "localhost";
    private static final int LOCAL_PORT = 5500;
    private WebView webView;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(246, 242, 234));
        getWindow().setNavigationBarColor(Color.rgb(246, 242, 234));
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(246, 242, 234));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setSupportZoom(false);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("http".equals(uri.getScheme())
                        && LOCAL_HOST.equals(uri.getHost())
                        && uri.getPort() == LOCAL_PORT) {
                    return serveBundledAsset(uri.getPath());
                }
                return super.shouldInterceptRequest(view, request);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if ("http".equals(uri.getScheme())
                        && LOCAL_HOST.equals(uri.getHost())
                        && uri.getPort() == LOCAL_PORT) {
                    return false;
                }
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (Exception ignored) {
                    // Keep the app usable if no external browser can handle the link.
                }
                return true;
            }
        });

        setContentView(webView);
        webView.loadUrl("http://localhost:5500/index.html");
    }

    private WebResourceResponse serveBundledAsset(String rawPath) {
        try {
            String path = URLDecoder.decode(rawPath == null ? "/" : rawPath, StandardCharsets.UTF_8);
            if (path.equals("/") || path.isEmpty()) path = "/index.html";
            if (path.contains("..") || path.startsWith("//")) {
                return response(403, "Forbidden", "text/plain", "Blocked path".getBytes(StandardCharsets.UTF_8));
            }

            String assetPath = "www/" + path.substring(1);
            InputStream stream = getAssets().open(assetPath);
            String mime = mimeType(path);
            String encoding = mime.startsWith("text/") || mime.contains("javascript")
                    || mime.contains("json") || mime.contains("svg") ? "UTF-8" : null;
            return new WebResourceResponse(mime, encoding, 200, "OK", Collections.emptyMap(), stream);
        } catch (IOException | IllegalArgumentException error) {
            return response(404, "Not Found", "text/plain",
                    "Asset not found".getBytes(StandardCharsets.UTF_8));
        }
    }

    private static WebResourceResponse response(int status, String reason, String mime, byte[] body) {
        return new WebResourceResponse(mime, "UTF-8", status, reason,
                Collections.emptyMap(), new java.io.ByteArrayInputStream(body));
    }

    private static String mimeType(String path) {
        String lower = path.toLowerCase();
        if (lower.endsWith(".html")) return "text/html";
        if (lower.endsWith(".css")) return "text/css";
        if (lower.endsWith(".js")) return "application/javascript";
        if (lower.endsWith(".json") || lower.endsWith(".webmanifest")) return "application/manifest+json";
        if (lower.endsWith(".svg")) return "image/svg+xml";
        if (lower.endsWith(".png")) return "image/png";
        if (lower.endsWith(".jpg") || lower.endsWith(".jpeg")) return "image/jpeg";
        if (lower.endsWith(".woff2")) return "font/woff2";
        return "application/octet-stream";
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
