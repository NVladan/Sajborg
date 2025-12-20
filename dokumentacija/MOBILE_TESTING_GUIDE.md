# 📱 Mobile Testing Guide & Checklist

**Date:** 2025-11-14
**Project:** Sajborg.com E-commerce Platform
**Status:** 🔄 Testing in Progress
**Server:** http://127.0.0.1:5000

---

## 📋 Testing Overview

This guide provides a comprehensive checklist for testing the mobile responsiveness of Sajborg.com. The mobile.css framework has been implemented and needs validation across different devices and viewports.

---

## 🎯 Test Devices & Viewports

### Mobile Devices (Portrait)
- **iPhone SE**: 375px × 667px
- **iPhone 12/13/14**: 390px × 844px
- **iPhone 14 Pro Max**: 430px × 932px
- **Samsung Galaxy S20**: 360px × 800px
- **Samsung Galaxy S21+**: 384px × 854px
- **Google Pixel 5**: 393px × 851px

### Mobile Devices (Landscape)
- **iPhone SE**: 667px × 375px
- **iPhone 12/13/14**: 844px × 390px

### Tablets (Portrait & Landscape)
- **iPad Mini**: 768px × 1024px
- **iPad Air**: 820px × 1180px
- **iPad Pro 11"**: 834px × 1194px
- **Samsung Galaxy Tab**: 800px × 1280px

---

## 🧪 How to Test Using Browser DevTools

### Chrome DevTools
1. Open Chrome and navigate to http://127.0.0.1:5000
2. Press `F12` or `Ctrl+Shift+I` (Windows) / `Cmd+Option+I` (Mac)
3. Click the device toolbar icon (or press `Ctrl+Shift+M` / `Cmd+Shift+M`)
4. Select device from dropdown or set custom dimensions
5. Test both portrait and landscape orientations
6. Test touch events by enabling "Touch" mode

### Firefox Responsive Design Mode
1. Open Firefox and navigate to http://127.0.0.1:5000
2. Press `Ctrl+Shift+M` (Windows) / `Cmd+Option+M` (Mac)
3. Select device from dropdown
4. Enable touch simulation
5. Test different viewport sizes

### Edge DevTools
1. Open Edge and navigate to http://127.0.0.1:5000
2. Press `F12` or `Ctrl+Shift+I`
3. Click "Toggle device emulation" (phone icon)
4. Select device preset or custom dimensions

---

## ✅ PAGE-BY-PAGE TESTING CHECKLIST

### 1. Homepage (`/`)

#### Visual Layout
- [ ] Hero section displays properly without excessive height
- [ ] Featured products show in single column on phones (<768px)
- [ ] Featured products show in 2 columns on tablets (768-991px)
- [ ] Category cards stack vertically on mobile
- [ ] Images scale properly and don't overflow
- [ ] Text remains readable (no tiny fonts)
- [ ] No horizontal scrolling

#### Touch Targets
- [ ] All buttons are minimum 44px height
- [ ] Category cards are easy to tap
- [ ] Navigation links have adequate spacing
- [ ] "View Products" buttons are easily tappable

#### Performance
- [ ] Page loads quickly on mobile
- [ ] Images load without layout shift
- [ ] No janky scrolling

**Test URLs:**
- http://127.0.0.1:5000/

---

### 2. Navigation Menu

#### Mobile Menu (<992px)
- [ ] Hamburger menu icon visible and tappable
- [ ] Menu expands/collapses smoothly
- [ ] Menu items stack vertically
- [ ] All menu items are easily tappable (44px+ height)
- [ ] Search bar expands to full width
- [ ] Cart icon visible with badge
- [ ] User profile dropdown works on mobile
- [ ] Menu backdrop works correctly

#### Search Functionality
- [ ] Search input has 16px font size (prevents iOS zoom)
- [ ] Search button is 44px+ and easily tappable
- [ ] Search results display properly on mobile
- [ ] Autocomplete doesn't break layout

**Test URLs:**
- Navigate from any page and test menu

---

### 3. Product Listing (`/proizvodi`)

#### Layout
- [ ] Products display in single column on phones (<576px)
- [ ] Products display in 2 columns on larger phones (576-767px)
- [ ] Filters sidebar becomes off-canvas on mobile
- [ ] Filter button is prominent and easily tappable
- [ ] Sort dropdown works properly
- [ ] Product cards have adequate spacing
- [ ] Product images scale correctly

#### Filters (Mobile)
- [ ] Filter button opens off-canvas sidebar
- [ ] Filters are easy to select on mobile
- [ ] Checkbox/radio buttons are 44px+ tap targets
- [ ] "Apply Filters" button is sticky at bottom
- [ ] Close filter button works correctly
- [ ] Category filter chips display properly

#### Product Cards
- [ ] Product images maintain aspect ratio
- [ ] Product name is readable (not truncated badly)
- [ ] Price is prominent
- [ ] "Add to Cart" button is 44px+ height
- [ ] "View Details" link is easily tappable
- [ ] Stock indicators display correctly

**Test URLs:**
- http://127.0.0.1:5000/proizvodi
- http://127.0.0.1:5000/proizvodi?category_slug=graficke-kartice
- Test with various filters applied

---

### 4. Product Detail Page (`/proizvodi/<slug>`)

#### Layout
- [ ] Product image gallery displays properly
- [ ] Main product image is properly sized (not too large)
- [ ] Thumbnail images are 60px × 60px and tappable
- [ ] Image gallery allows swiping (if implemented)
- [ ] Product title is readable
- [ ] Price is prominent

#### Product Information
- [ ] Specifications table doesn't overflow
- [ ] Specifications table is horizontally scrollable if needed
- [ ] Description text is readable
- [ ] All sections stack vertically

#### Actions
- [ ] Quantity controls are 44px+ and easy to tap
- [ ] "Add to Cart" button is 48px+ height
- [ ] "Add to Cart" button is full-width or prominently placed
- [ ] Review section displays properly
- [ ] Review form inputs are 16px font size

#### Reviews
- [ ] Reviews display in readable format
- [ ] Star ratings are visible
- [ ] Review submission form works on mobile
- [ ] Text area is adequately sized

**Test URLs:**
- http://127.0.0.1:5000/proizvodi/[any-product-slug]
- Test with products that have multiple images
- Test with products that have many specifications

---

### 5. Shopping Cart (`/cart`)

#### Layout
- [ ] Cart items display in single column
- [ ] Each cart item card is properly formatted
- [ ] Product image scales appropriately
- [ ] Product name is readable
- [ ] Price displays clearly

#### Quantity Controls
- [ ] Quantity +/- buttons are 44px+ and easily tappable
- [ ] Quantity input is readable (16px font)
- [ ] Remove button is 44px+ and clearly visible
- [ ] Update cart button works correctly

#### Cart Summary
- [ ] Cart summary is sticky at bottom OR properly positioned
- [ ] Subtotal/Total displays prominently
- [ ] "Proceed to Checkout" button is 48px+ height
- [ ] "Proceed to Checkout" button is easily accessible
- [ ] "Continue Shopping" link is visible

#### Empty Cart
- [ ] Empty cart message displays properly
- [ ] "Browse Products" button is prominent
- [ ] Icon displays correctly

**Test URLs:**
- http://127.0.0.1:5000/cart
- Test with 1 item, multiple items, and empty cart

---

### 6. Checkout Page (`/checkout`)

#### Layout
- [ ] Checkout form displays in single column
- [ ] Step indicators (if present) are clear on mobile
- [ ] Form sections are clearly separated
- [ ] Order summary is accessible

#### Form Inputs
- [ ] All inputs have 16px font size (prevents zoom on iOS)
- [ ] Input fields have adequate height (44px+)
- [ ] Labels are clearly associated with inputs
- [ ] Error messages display properly
- [ ] Required field indicators are visible

#### Form Sections
- [ ] Shipping address section is easy to fill
- [ ] Payment method selection is clear
- [ ] Billing address section works correctly
- [ ] All dropdowns/selects work on mobile

#### Order Summary
- [ ] Order summary is visible (sticky or above form)
- [ ] Item list is readable
- [ ] Prices are clearly displayed
- [ ] Total is prominent

#### Actions
- [ ] "Place Order" button is 48px+ height
- [ ] "Place Order" button is prominently placed
- [ ] "Back to Cart" link is accessible
- [ ] Form validation works correctly

**Test URLs:**
- http://127.0.0.1:5000/checkout
- Test form validation
- Test with different number of items

---

### 7. PC Builder (`/pc-builder`)

#### Layout
- [ ] Component type tabs display properly on mobile
- [ ] Tabs scroll horizontally if needed
- [ ] Component cards display in single column
- [ ] Build summary is accessible

#### Component Selection
- [ ] Component cards are properly sized
- [ ] Component images scale correctly
- [ ] "Add to Build" buttons are 44px+ and easily tappable
- [ ] Component specs are readable
- [ ] Price displays clearly

#### Build Summary
- [ ] Build summary is sticky or easily accessible
- [ ] Selected components list is readable
- [ ] Total price is prominent
- [ ] "Remove" buttons are 44px+ and easily tappable
- [ ] Compatibility warnings display clearly

#### Actions
- [ ] "Save Configuration" button is easily accessible
- [ ] "Add to Cart" button is prominent
- [ ] "Clear Build" button is clearly visible
- [ ] Modal dialogs work correctly on mobile

#### Saved Configurations
- [ ] Saved builds list displays properly
- [ ] "Load" buttons are easily tappable
- [ ] Configuration details are readable

**Test URLs:**
- http://127.0.0.1:5000/pc-builder
- Test building a complete PC
- Test loading saved configuration

---

### 8. User Profile (`/profile`)

#### Layout
- [ ] Profile form displays in single column
- [ ] Avatar/profile image displays correctly
- [ ] Form sections are clearly separated

#### Form Inputs
- [ ] All inputs have 16px font size
- [ ] Input fields have adequate height (44px+)
- [ ] Edit buttons are easily tappable
- [ ] Save button is prominent (48px+ height)

#### Order History
- [ ] Order list displays properly
- [ ] Order cards are readable on mobile
- [ ] "View Details" links are easily tappable
- [ ] Order dates and totals are visible

**Test URLs:**
- http://127.0.0.1:5000/profile
- Test editing profile information

---

### 9. Authentication Pages

#### Login (`/auth/login`)
- [ ] Login form displays properly
- [ ] Email/username input is 16px font
- [ ] Password input is 16px font
- [ ] Input fields are 44px+ height
- [ ] "Login" button is 48px+ height and prominent
- [ ] "Forgot Password" link is easily tappable
- [ ] "Register" link is visible

#### Registration (`/auth/register`)
- [ ] Registration form displays in single column
- [ ] All inputs have 16px font size
- [ ] Input fields have adequate height (44px+)
- [ ] Password requirements are clearly displayed
- [ ] "Register" button is prominent
- [ ] "Already have account" link is visible

**Test URLs:**
- http://127.0.0.1:5000/auth/login
- http://127.0.0.1:5000/auth/register

---

### 10. Blog/Tech Magazin (`/blog`)

#### Layout
- [ ] Blog posts display in single column on mobile
- [ ] Featured images scale properly
- [ ] Post titles are readable
- [ ] Post excerpts display correctly
- [ ] "Read More" buttons are easily tappable

#### Single Post
- [ ] Article content is readable
- [ ] Images in content scale properly
- [ ] Code blocks (if any) are horizontally scrollable
- [ ] Share buttons are 44px+ and easily tappable
- [ ] Comments section works on mobile

**Test URLs:**
- http://127.0.0.1:5000/blog
- http://127.0.0.1:5000/blog/[post-slug]

---

### 11. Footer

#### Layout
- [ ] Footer sections stack vertically on mobile
- [ ] Newsletter signup form displays properly
- [ ] Email input is 16px font size
- [ ] Submit button is easily tappable
- [ ] Social media icons are 44px+ and easily tappable

#### Links
- [ ] All footer links are easily tappable
- [ ] Links have adequate spacing
- [ ] Category links are readable

**Test on all pages**

---

### 12. Admin Panel (`/admin`)

#### Layout
- [ ] Admin dashboard displays reasonably on tablet
- [ ] Sidebar navigation works on mobile
- [ ] Data tables are horizontally scrollable
- [ ] Action buttons are easily tappable

#### Forms
- [ ] Admin forms work on mobile
- [ ] File upload buttons are easily tappable
- [ ] Rich text editors (if any) work on mobile

**Note:** Admin panel may not be fully optimized for mobile as it's typically used on desktop

---

## 🔍 CRITICAL ISSUES TO CHECK

### Typography & Readability
- [ ] Base font size is at least 16px (prevents iOS zoom)
- [ ] All form inputs are 16px font size
- [ ] Headings scale appropriately (h1: 1.75rem, h2: 1.5rem, h3: 1.25rem)
- [ ] Line height is adequate for mobile reading (1.5-1.6)
- [ ] Text contrast is sufficient (WCAG AA minimum)

### Touch Targets
- [ ] All buttons are minimum 44px × 44px
- [ ] All links have adequate tap area
- [ ] Form inputs are minimum 44px height
- [ ] Checkboxes/radio buttons are 44px × 44px
- [ ] Quantity controls are 44px × 44px

### Layout & Spacing
- [ ] No horizontal scrolling (except intentional, like tables)
- [ ] Adequate padding/margin on mobile (15px container padding)
- [ ] Cards have proper spacing (1rem margin-bottom)
- [ ] Sections have proper spacing (2rem padding)
- [ ] Content doesn't touch screen edges

### Forms
- [ ] All inputs prevent iOS auto-zoom (16px font minimum)
- [ ] Labels are clearly visible
- [ ] Error messages display properly
- [ ] Required fields are indicated
- [ ] Submit buttons are prominent and easily tappable

### Images & Media
- [ ] All images scale properly (max-width: 100%)
- [ ] Images maintain aspect ratio
- [ ] Product images are properly sized (max-height on mobile)
- [ ] Gallery thumbnails are 60px × 60px
- [ ] No broken image links

### Navigation
- [ ] Hamburger menu works correctly
- [ ] Mobile menu opens/closes smoothly
- [ ] Menu items are easily tappable
- [ ] Active page is indicated
- [ ] Cart badge displays correctly

### Modals & Overlays
- [ ] Modals display properly on mobile
- [ ] Modal content is scrollable if needed
- [ ] Close button is easily tappable
- [ ] Backdrop works correctly
- [ ] Flash messages display properly

### Performance
- [ ] Pages load quickly on simulated 3G
- [ ] No layout shift during page load
- [ ] Smooth scrolling (no jank)
- [ ] Images lazy load if implemented
- [ ] No excessive JavaScript execution time

---

## 🐛 COMMON MOBILE ISSUES TO WATCH FOR

### iOS-Specific
- [ ] Auto-zoom on input focus (fix: 16px font size)
- [ ] Fixed positioning issues (iOS Safari)
- [ ] 100vh viewport height issues
- [ ] Tap highlight color
- [ ] Smooth scrolling on fixed elements

### Android-Specific
- [ ] Address bar hiding/showing causing layout issues
- [ ] Tap delay (should be removed with modern browsers)
- [ ] Form validation appearance
- [ ] Select dropdown appearance

### Cross-Platform
- [ ] Hover states don't work on touch (ensure tap alternatives)
- [ ] Landscape orientation issues
- [ ] Long press behavior on links/buttons
- [ ] Scroll momentum (should feel native)
- [ ] Virtual keyboard covering inputs

---

## 📊 TESTING METHODOLOGY

### 1. Visual Inspection
For each page and viewport size:
1. Load the page
2. Check overall layout
3. Verify no horizontal scrolling
4. Check font sizes are readable
5. Verify images display correctly
6. Check spacing and alignment

### 2. Interaction Testing
For each interactive element:
1. Tap/click buttons
2. Fill out forms
3. Use navigation
4. Test dropdowns/selects
5. Verify modals/overlays
6. Test quantity controls

### 3. Performance Testing
For each page:
1. Open DevTools Network tab
2. Throttle to "Fast 3G"
3. Reload page
4. Check load time
5. Monitor layout shifts
6. Test scrolling performance

### 4. Cross-Browser Testing
Test on multiple browsers:
1. Chrome Mobile (Android)
2. Safari Mobile (iOS)
3. Firefox Mobile
4. Samsung Internet

---

## 📝 ISSUE TRACKING TEMPLATE

When you find an issue, document it using this format:

```markdown
### Issue: [Brief Description]
**Page:** [URL or page name]
**Device:** [Viewport size or device]
**Browser:** [Browser name and version]
**Severity:** [Critical / High / Medium / Low]

**Description:**
[Detailed description of the issue]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Screenshot/Video:**
[If available]

**Suggested Fix:**
[Proposed solution, if known]
```

---

## ✅ TESTING COMPLETION CRITERIA

Mobile testing is considered complete when:

1. ✅ All pages tested on at least 3 mobile viewport sizes
2. ✅ All pages tested on at least 2 tablet viewport sizes
3. ✅ All pages tested in portrait and landscape
4. ✅ All critical user flows work on mobile (browse → add to cart → checkout)
5. ✅ No horizontal scrolling on any page
6. ✅ All touch targets meet 44px minimum
7. ✅ All forms work correctly on mobile
8. ✅ Navigation works smoothly on mobile
9. ✅ No critical issues remaining
10. ✅ Performance is acceptable on simulated 3G

---

## 🎯 PRIORITY TEST FLOWS

### Critical User Flow 1: Browse and Purchase
1. Open homepage on iPhone SE (375px)
2. Navigate to product listing
3. Apply filters
4. View product detail
5. Add product to cart
6. View cart
7. Proceed to checkout
8. Fill out checkout form

**Success Criteria:** Can complete entire flow without issues

### Critical User Flow 2: PC Builder
1. Open PC Builder on iPad (768px)
2. Select components for each category
3. View build summary
4. Save configuration
5. Load configuration
6. Add build to cart

**Success Criteria:** Can build and save PC configuration on tablet

### Critical User Flow 3: User Account
1. Open registration page on Galaxy S21 (384px)
2. Register new account
3. Login
4. Edit profile
5. View order history
6. Logout

**Success Criteria:** All account operations work smoothly

---

## 📈 SUCCESS METRICS

Track these metrics during testing:

- **Load Time (3G):** < 5 seconds
- **First Contentful Paint:** < 2 seconds
- **Time to Interactive:** < 4 seconds
- **Cumulative Layout Shift:** < 0.1
- **Touch Target Compliance:** 100% (all interactive elements ≥ 44px)
- **Viewport Issues:** 0 horizontal scroll instances
- **Form Issues:** 0 iOS zoom issues
- **Critical Bugs:** 0 blocking issues

---

## 🚀 NEXT STEPS AFTER TESTING

1. Document all issues found
2. Prioritize issues (Critical → High → Medium → Low)
3. Fix critical and high-priority issues
4. Re-test fixed issues
5. Update mobile.css as needed
6. Update MOBILE_RESPONSIVENESS.md with results
7. Mark Phase 2 as complete in TODOLIST.md

---

**Testing Started:** 2025-11-14
**Tested By:** [Your name]
**Status:** 🔄 In Progress
**Server:** http://127.0.0.1:5000

---

**End of Testing Guide**
