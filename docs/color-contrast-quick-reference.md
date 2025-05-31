# Color Contrast Quick Reference Guide

## WCAG Compliance Cheat Sheet

### Standards
- **WCAG AA** (Required): 4.5:1 normal text, 3:1 large text/UI
- **WCAG AAA** (Best Practice): 7:1 normal text, 4.5:1 large text

### Quick Audit
```bash
# Test current localhost
npm run audit:contrast

# Test with report
npm run audit:contrast:report
```

## Color Token System

### Text Colors (Use These!)
```jsx
// Primary content - highest contrast
<h1 className="text-text-primary dark:text-white">Main Heading</h1>

// Secondary content - good contrast  
<p className="text-text-secondary dark:text-text-secondary">Description text</p>

// Tertiary content - labels, captions
<span className="text-text-tertiary dark:text-text-tertiary">Caption</span>

// Muted content - helper text
<small className="text-text-muted dark:text-text-muted">Helper text</small>
```

### Links
```jsx
// Standard links
<a className="text-link-primary hover:text-link-hover dark:text-link-dark dark:hover:text-link-dark-hover">
  Link text
</a>
```

### Buttons
```jsx
// Primary buttons - AAA compliant
<button className="bg-primary-800 hover:bg-primary-900 text-white">
  Primary Action
</button>

// Secondary buttons
<button className="bg-gray-200 hover:bg-gray-300 text-gray-900">
  Secondary Action  
</button>
```

### Notifications
```jsx
// Use the Notification component with proper types
<Notification type="success" message="Success message" />
<Notification type="error" message="Error message" />
<Notification type="warning" message="Warning message" />
<Notification type="info" message="Info message" />
```

## Don't Use (Legacy Colors)

❌ **Avoid these classes:**
- `text-gray-600`, `text-gray-700` → Use `text-text-secondary`
- `text-blue-600`, `text-indigo-600` → Use `text-link-primary`  
- `bg-indigo-600` → Use `bg-primary-800`
- Direct color values → Use semantic tokens

## Testing Checklist

### Before Committing
1. ✅ Run `npm run audit:contrast`
2. ✅ Test both light and dark modes
3. ✅ Check focus states are visible
4. ✅ Verify text is readable

### New Components
1. ✅ Use color tokens from the start
2. ✅ Test with screen reader if possible
3. ✅ Ensure 44px+ touch targets on mobile
4. ✅ Add to audit script test scenarios if needed

## Common Fixes

### Low Contrast Text
```jsx
// ❌ Before
<p className="text-gray-500">Helper text</p>

// ✅ After  
<p className="text-text-muted dark:text-text-muted">Helper text</p>
```

### Poor Link Contrast
```jsx
// ❌ Before
<a className="text-blue-500 hover:text-blue-700">Link</a>

// ✅ After
<a className="text-link-primary hover:text-link-hover dark:text-link-dark dark:hover:text-link-dark-hover">Link</a>
```

### Button Contrast Issues
```jsx
// ❌ Before  
<button className="bg-blue-500 text-white">Submit</button>

// ✅ After
<button className="bg-primary-800 hover:bg-primary-900 text-white">Submit</button>
```

## Emergency Contrast Fixes

If you need a quick fix for contrast issues:

```jsx
// Quick high-contrast text
className="text-gray-900 dark:text-white"

// Quick high-contrast link
className="text-blue-800 dark:text-blue-200"

// Quick button fix
className="bg-gray-900 text-white hover:bg-gray-800"
```

## Useful Tools

- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Chrome DevTools**: Inspect Element → Accessibility tab shows contrast ratio
- **Figma Plugin**: "Stark" for checking designs

---

💡 **Remember**: Accessibility isn't just compliance—it makes our app better for everyone! 