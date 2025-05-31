# Color Contrast Audit Report

**Audit Date:** 31/5/2025  
**Total Scenarios:** 14  
**Scenarios with Violations:** 14  
**Total Violations:** 14

## Summary

❌ **14 contrast violation(s) found** across 14 scenario(s).

## Detailed Results

### ❌ URL Input Panel - Initial State (light)

- **Description:** Landing page with URL input form
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ URL Input Panel - Error State (light)

- **Description:** URL input with validation error displayed
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ URL Input Panel - Loading State (light)

- **Description:** URL input in loading/disabled state
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Notification - Success Toast (light)

- **Description:** Success notification toast
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `h4`
   **HTML:** `<h4 class="font-medium">Success</h4>`
   **Issue:** Element has insufficient color contrast of 6.81 (foreground color: #016630, background color: #f0fdf4, font size: 12.0pt (16px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.items-start.flex > div > p`
   **HTML:** `<p class="text-sm">Operation completed successfully</p>`
   **Issue:** Element has insufficient color contrast of 6.81 (foreground color: #016630, background color: #f0fdf4, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Notification - Error Toast (light)

- **Description:** Error notification toast
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Notification - Warning Banner (light)

- **Description:** Warning notification banner
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `h4`
   **HTML:** `<h4 class="font-medium">Warning</h4>`
   **Issue:** Element has insufficient color contrast of 6.62 (foreground color: #894b00, background color: #fefce8, font size: 12.0pt (16px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.items-start.flex > div > p`
   **HTML:** `<p class="text-sm">Please review your input</p>`
   **Issue:** Element has insufficient color contrast of 6.62 (foreground color: #894b00, background color: #fefce8, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Modal Placeholder (light)

- **Description:** Modal dialog with download link
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.41 (foreground color: #1d4ed8, background color: #f9fafb, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `.flex-1.bg-indigo-600.hover\:bg-indigo-700`
   **HTML:** `<button class="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:ring-2...`
   **Issue:** Element has insufficient color contrast of 6.46 (foreground color: #ffffff, background color: #4f39f6, font size: 12.0pt (16px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ URL Input Panel - Initial State (dark)

- **Description:** Landing page with URL input form
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.text-lg`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.text-text-tertiary`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ URL Input Panel - Error State (dark)

- **Description:** URL input with validation error displayed
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.text-lg`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.text-text-tertiary`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ URL Input Panel - Loading State (dark)

- **Description:** URL input in loading/disabled state
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.text-lg`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.mt-1`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Notification - Success Toast (dark)

- **Description:** Success notification toast
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.text-lg`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.text-text-tertiary`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Notification - Error Toast (dark)

- **Description:** Error notification toast
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.text-lg`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.text-text-tertiary`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Notification - Warning Banner (dark)

- **Description:** Warning notification banner
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.text-lg`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.text-text-tertiary`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

---

### ❌ Modal Placeholder (dark)

- **Description:** Modal dialog with download link
- **URL:** http://localhost:3001/
- **Violations:** 1

#### Violation 1: color-contrast-enhanced

**Description:** Ensure the contrast between foreground and background colors meets WCAG 2 AAA enhanced contrast ratio thresholds

**Impact:** serious

**Help:** Elements must meet enhanced color contrast ratio thresholds

**Affected Elements:**

1. **Selector:** `.max-w-2xl`
   **HTML:** `<p class="text-lg text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">Paste a video URL from YouTube...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 13.5pt (18px), font weight: normal). Expected contrast ratio of 7:1

2. **Selector:** `.text-text-tertiary`
   **HTML:** `<p class="text-xs mt-1 text-text-tertiary dark:text-gray-400">Rate limits: 10 requests per minute • ...`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

3. **Selector:** `a[href$="terms"]`
   **HTML:** `<a href="/terms" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-link-...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

4. **Selector:** `a[href$="privacy"]`
   **HTML:** `<a href="/privacy" target="_blank" rel="noopener noreferrer" class="text-link-primary hover:text-lin...`
   **Issue:** Element has insufficient color contrast of 6.98 (foreground color: #60a5fa, background color: #101828, font size: 10.5pt (14px), font weight: normal). Expected contrast ratio of 7:1

5. **Selector:** `.text-xs.text-text-secondary.dark\:text-gray-400 > p`
   **HTML:** `<p>© 2024 Meme Maker • Free video clipping tool</p>`
   **Issue:** Element has insufficient color contrast of 6.82 (foreground color: #99a1af, background color: #101828, font size: 9.0pt (12px), font weight: normal). Expected contrast ratio of 7:1

6. **Selector:** `nextjs-portal,button[data-issues-open="true"] > div:nth-child(2)`
   **HTML:** `<div>Issue</div>`
   **Issue:** Element has insufficient color contrast of 5.4 (foreground color: #ffffff, background color: #ca2a30, font size: 9.8pt (13px), font weight: normal). Expected contrast ratio of 7:1

7. **Selector:** `.text-gray-600.mb-4.dark\:text-gray-400`
   **HTML:** `<p class="text-gray-600 dark:text-gray-400 mb-4">Your clip is ready for download</p>`
   **Issue:** Element has insufficient color contrast of 5.63 (foreground color: #99a1af, background color: #1e2939, font size: 12.0pt (16px), font weight: normal). Expected contrast ratio of 7:1

8. **Selector:** `.flex-1.bg-indigo-600.hover\:bg-indigo-700`
   **HTML:** `<button class="flex-1 bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:ring-2...`
   **Issue:** Element has insufficient color contrast of 6.46 (foreground color: #ffffff, background color: #4f39f6, font size: 12.0pt (16px), font weight: normal). Expected contrast ratio of 7:1

9. **Selector:** `.dark\:bg-gray-600`
   **HTML:** `<button class="bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-200 py-2 px-4 rounded-md ho...`
   **Issue:** Element has insufficient color contrast of 6.1 (foreground color: #e5e7eb, background color: #4a5565, font size: 12.0pt (16px), font weight: normal). Expected contrast ratio of 7:1

---

