/**
 * generatePolicyPdf
 * Generates and downloads a policy document PDF entirely in the browser.
 * No external library required — uses a hidden iframe + window.print().
 *
 * @param {Object} policy  — the policy object from policyData.js
 * @param {string} category — e.g. 'health', 'motor', 'agriculture', 'property'
 */
export function generatePolicyPdf(policy, category = 'insurance') {
  const refNo = `CF-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).slice(2, 6).toUpperCase()}`;
  const issuedDate = new Date().toLocaleDateString('en-IN', {
    day: '2-digit', month: 'long', year: 'numeric',
  });

  const features = (policy.features ?? [])
    .map((f) => `<li style="margin-bottom:6px;">&#10003;&nbsp; ${f}</li>`)
    .join('');

  const missingFeatures = (policy.missingFeatures ?? [])
    .map((f) => `<li style="margin-bottom:6px; color:#ba1a1a;">&#10007;&nbsp; <s>${f}</s></li>`)
    .join('');

  const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>ClaimFlow Policy Document — ${policy.name ?? 'Policy'}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700;800&family=Work+Sans:wght@400;500;600&display=swap');

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: 'Work Sans', Arial, sans-serif;
      color: #191c1e;
      background: #fff;
      padding: 0;
    }

    /* ── Header ── */
    .header {
      background: #002045;
      color: #fff;
      padding: 32px 48px 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .brand {
      font-family: 'Be Vietnam Pro', Arial, sans-serif;
      font-size: 26px;
      font-weight: 800;
      color: #fea619;
      letter-spacing: -0.5px;
    }
    .brand-sub {
      font-size: 12px;
      color: rgba(255,255,255,0.6);
      margin-top: 2px;
    }
    .doc-type {
      text-align: right;
    }
    .doc-type h1 {
      font-family: 'Be Vietnam Pro', Arial, sans-serif;
      font-size: 20px;
      font-weight: 700;
      color: #ffddb8;
    }
    .doc-type p {
      font-size: 12px;
      color: rgba(255,255,255,0.6);
      margin-top: 4px;
    }

    /* ── Reference strip ── */
    .ref-strip {
      background: #1a365d;
      color: #86a0cd;
      padding: 10px 48px;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
    }
    .ref-strip span { color: #ffddb8; font-weight: 600; }

    /* ── Body ── */
    .body { padding: 36px 48px; }

    /* ── Policy name block ── */
    .policy-name-block {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding-bottom: 24px;
      border-bottom: 2px solid #eceef0;
      margin-bottom: 28px;
    }
    .policy-name {
      font-family: 'Be Vietnam Pro', Arial, sans-serif;
      font-size: 28px;
      font-weight: 700;
      color: #002045;
    }
    .badge {
      background: #ffddb8;
      color: #653e00;
      padding: 4px 12px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      margin-top: 6px;
      display: inline-block;
    }
    .price-block { text-align: right; }
    .price-label { font-size: 12px; color: #74777f; }
    .price-original { font-size: 13px; color: #74777f; text-decoration: line-through; }
    .price-main {
      font-family: 'Be Vietnam Pro', Arial, sans-serif;
      font-size: 32px;
      font-weight: 700;
      color: #002045;
    }
    .price-period { font-size: 14px; font-weight: 400; color: #43474e; }
    .price-saving { font-size: 13px; color: #855300; font-weight: 700; margin-top: 2px; }
    .price-note { font-size: 12px; color: #43474e; margin-top: 2px; }

    /* ── Rating ── */
    .rating {
      font-size: 13px;
      color: #855300;
      margin-top: 6px;
    }

    /* ── Two-column grid ── */
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 28px; }

    /* ── Section ── */
    .section { margin-bottom: 28px; }
    .section-title {
      font-family: 'Be Vietnam Pro', Arial, sans-serif;
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #74777f;
      margin-bottom: 12px;
      padding-bottom: 6px;
      border-bottom: 1px solid #eceef0;
    }
    .features-list {
      list-style: none;
      font-size: 14px;
      color: #191c1e;
      line-height: 1.6;
    }

    /* ── Highlight box ── */
    .highlight-box {
      background: #f2f4f6;
      border-left: 4px solid #fea619;
      padding: 14px 18px;
      border-radius: 0 8px 8px 0;
      margin-bottom: 28px;
    }
    .highlight-box.premium {
      background: #003762/10;
      border-left-color: #58a2f0;
    }
    .highlight-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #74777f;
      margin-bottom: 4px;
    }
    .highlight-text {
      font-size: 14px;
      color: #002045;
      font-style: italic;
    }

    /* ── Terms ── */
    .terms {
      background: #f7f9fb;
      border: 1px solid #c4c6cf;
      border-radius: 8px;
      padding: 16px 20px;
      font-size: 11px;
      color: #74777f;
      line-height: 1.6;
      margin-bottom: 28px;
    }
    .terms strong { color: #43474e; }

    /* ── Footer ── */
    .footer {
      background: #002045;
      color: rgba(255,255,255,0.5);
      padding: 16px 48px;
      font-size: 11px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .footer a { color: #86a0cd; text-decoration: none; }

    /* ── Print ── */
    @media print {
      body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
      @page { margin: 0; size: A4; }
    }
  </style>
</head>
<body>

  <!-- Header -->
  <div class="header">
    <div>
      <div class="brand">ClaimFlow</div>
      <div class="brand-sub">Insurance Management Platform</div>
    </div>
    <div class="doc-type">
      <h1>Policy Document</h1>
      <p>Category: ${category.charAt(0).toUpperCase() + category.slice(1)} Insurance</p>
    </div>
  </div>

  <!-- Reference strip -->
  <div class="ref-strip">
    <div>Reference No: <span>${refNo}</span></div>
    <div>Issued: <span>${issuedDate}</span></div>
    <div>Status: <span>Quote Generated</span></div>
  </div>

  <!-- Body -->
  <div class="body">

    <!-- Policy name + price -->
    <div class="policy-name-block">
      <div>
        <div class="policy-name">${policy.name ?? 'Insurance Policy'}</div>
        ${policy.badge ? `<div class="badge">${policy.badge}</div>` : ''}
        ${policy.rating ? `<div class="rating">&#9733; ${policy.rating} &nbsp;(${policy.reviews} reviews)</div>` : ''}
      </div>
      <div class="price-block">
        <div class="price-label">Annual Premium</div>
        ${policy.originalPrice ? `<div class="price-original">${policy.originalPrice}</div>` : ''}
        <div class="price-main">${policy.price ?? policy.premium ?? '—'} <span class="price-period">/yr</span></div>
        ${policy.saving ? `<div class="price-saving">${policy.saving}</div>` : ''}
        ${policy.note ? `<div class="price-note">${policy.note}</div>` : ''}
      </div>
    </div>

    <!-- Features -->
    <div class="two-col">
      <div class="section">
        <div class="section-title">Coverage Includes</div>
        <ul class="features-list">${features || '<li>—</li>'}</ul>
      </div>
      ${missingFeatures ? `
      <div class="section">
        <div class="section-title">Not Covered</div>
        <ul class="features-list">${missingFeatures}</ul>
      </div>` : '<div></div>'}
    </div>

    <!-- Highlight -->
    ${policy.highlight ? `
    <div class="highlight-box ${policy.highlightVariant === 'premium' ? 'premium' : ''}">
      <div class="highlight-label">${policy.highlightVariant === 'premium' ? 'Premium Service' : 'Key Highlight'}</div>
      <div class="highlight-text">"${policy.highlight}"</div>
    </div>` : ''}

    <!-- Terms -->
    <div class="terms">
      <strong>Important Notice:</strong> This document is a quote summary generated by ClaimFlow and does not constitute a binding insurance contract.
      Final policy terms, conditions, and premium are subject to underwriting approval by the respective insurer.
      All prices shown are indicative and inclusive of applicable GST. Please read the policy wordings carefully before purchase.
      IRDAI Registration No. 123 &nbsp;|&nbsp; ClaimFlow Insurance Broking Pvt. Ltd.
    </div>

    <!-- Signature block -->
    <div class="two-col" style="margin-top:32px;">
      <div>
        <div style="border-top:1px solid #c4c6cf; padding-top:8px; font-size:12px; color:#74777f;">
          Customer Signature
        </div>
      </div>
      <div>
        <div style="border-top:1px solid #c4c6cf; padding-top:8px; font-size:12px; color:#74777f; text-align:right;">
          Authorised Signatory — ClaimFlow
        </div>
      </div>
    </div>

  </div>

  <!-- Footer -->
  <div class="footer">
    <div>© 2024 ClaimFlow Insurance. All rights reserved.</div>
    <div>
      <a href="#">Privacy Policy</a> &nbsp;|&nbsp;
      <a href="#">Terms of Service</a> &nbsp;|&nbsp;
      <a href="#">Compliance</a>
    </div>
    <div>Ref: ${refNo}</div>
  </div>

</body>
</html>`;

  // ── Trigger print-to-PDF via hidden iframe ────────────────────────────────
  const iframe = document.createElement('iframe');
  iframe.style.cssText = 'position:fixed;top:-9999px;left:-9999px;width:0;height:0;border:none;';
  document.body.appendChild(iframe);

  const doc = iframe.contentDocument || iframe.contentWindow.document;
  doc.open();
  doc.write(html);
  doc.close();

  // Wait for fonts/images to load, then print
  iframe.onload = () => {
    setTimeout(() => {
      iframe.contentWindow.focus();
      iframe.contentWindow.print();
      // Clean up after print dialog closes
      setTimeout(() => document.body.removeChild(iframe), 2000);
    }, 400);
  };
}
