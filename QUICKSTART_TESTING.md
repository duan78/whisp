# Quick Start Testing Guide - Whisp Frontend v2.0

## 🚀 Quick Start

### 1. Start the Application

```bash
# From your whisp directory
python app.py
```

### 2. Open in Browser

Navigate to: `http://localhost:5000` (or your configured port)

### 3. Test the New Features

#### Test Chat Interface

1. **Navigate to Conversation Tab**
   - Click the "Conversation" tab button (icon: 💬)
   - You should see:
     - Audio visualizer at top
     - Chat interface with message area
     - Text input field at bottom
     - Control buttons (Search, Export, Clear)

2. **Test Voice Commands**
   - Click the microphone button to activate
   - Speak a command (e.g., "écris", "quelle heure")
   - Messages should appear in chat bubbles
   - User commands appear on right (blue)
   - System responses appear on left (gray)
   - Errors appear in red

3. **Test Text Input**
   - Type in the text input field at bottom
   - Press Enter or click send button
   - Command should be processed

4. **Test Search**
   - Click "Rechercher" button
   - Search bar should appear
   - Type in search box
   - Messages should filter
   - Use checkboxes to filter by type

5. **Test Export**
   - Click "Exporter" button
   - JSON file should download
   - File should contain conversation history

6. **Test Clear**
   - Click "Effacer" button
   - Confirmation dialog should appear
   - Messages should clear after confirmation

#### Test Audio Visualizer

1. **Check States**
   - Idle: Horizontal line with "Prêt à écouter"
   - Listening: Animated bars when recording
   - Processing: Spinning indicator
   - Error: Error state display

2. **Check Theme**
   - Toggle dark mode if available
   - Visualizer should adapt colors

#### Test Accessibility

1. **Keyboard Navigation**
   - Press `Tab` to navigate through interface
   - Focus should be clearly visible (3px blue outline)
   - All interactive elements should be reachable

2. **Keyboard Shortcuts**
   - `Alt+Shift+M` - Toggle microphone
   - `Alt+Shift+H` - Show help
   - `Alt+Shift+C` - Focus chat input
   - `Alt+Shift+T` - Toggle theme
   - `Escape` - Close modals

3. **Screen Reader**
   - Enable NVDA/VoiceOver/TalkBack
   - Navigate through interface
   - States should be announced
   - New messages should be announced

4. **Skip Links**
   - Press `Tab` at page load
   - Skip links should appear at top
   - "Aller au contenu principal"
   - "Aller au panneau de contrôle"

#### Test Theme Switching

1. **Toggle Dark Mode**
   - Use theme toggle button or `Alt+Shift+T`
   - Colors should transition smoothly
   - All elements should remain readable
   - Contrast should remain high

#### Test Configuration

1. **Open Config Page**
   - Navigate to Configuration page
   - Test STT/TTS engine switching
   - Test parameter changes
   - Verify persistence

## ✅ Expected Behavior

### Visual Indicators

✅ **Success States**
- Green badges for success
- Smooth transitions
- Clear visual feedback
- Consistent spacing

✅ **Error States**
- Red error messages
- Clear error descriptions
- Accessible error announcements

✅ **Loading States**
- Spinners or progress indicators
- Disabled state during operations
- Clear status messages

### Responsive Design

✅ **Desktop (>768px)**
- Full chat interface
- All controls visible
- Text labels on buttons

✅ **Mobile (<768px)**
- Stacked layout
- Icon-only buttons
- Full-width inputs
- Touch-friendly targets (44px min)

## 🐛 Common Issues

### Issue: Chat interface not loading

**Solution:**
1. Check browser console for errors
2. Verify `chat-interface.js` is loaded
3. Check that `chat-interface.html` template exists
4. Verify SSE events are being dispatched

### Issue: Audio visualizer not showing

**Solution:**
1. Check browser supports Canvas
2. Verify `audio-visualizer.js` is loaded
3. Check canvas element exists in DOM
4. Look for JavaScript errors in console

### Issue: Theme not switching

**Solution:**
1. Check `style-modern.css` is loaded
2. Verify data-theme attribute changes
3. Check for CSS conflicts
4. Clear browser cache

### Issue: Keyboard shortcuts not working

**Solution:**
1. Verify `accessibility-shortcuts.js` is loaded
2. Check for conflicting keybindings
3. Ensure document has focus
4. Check browser console for errors

### Issue: Messages not appearing

**Solution:**
1. Check `/get_logs` endpoint exists
2. Verify SSE events are dispatched
3. Check browser console for errors
4. Verify `chat-interface.js` initialized

## 🔍 Debug Mode

### Enable Debug Logging

Open browser console and run:

```javascript
// Check if modules loaded
console.log('Chat Interface:', window.chatInterface);
console.log('Audio Visualizer:', window.audioVisualizer);
console.log('Config Manager:', window.configManager);
console.log('Shortcuts:', window.accessibilityShortcuts);

// Test adding message manually
window.chatInterface?.addMessage('Test message', 'info');

// Check theme
console.log('Current theme:', document.documentElement.getAttribute('data-theme'));
```

### Network Tab

1. Open DevTools (F12)
2. Go to Network tab
3. Check for failed requests:
   - `style-modern.css`
   - `chat-interface.js`
   - `audio-visualizer.js`
   - etc.

### Console Errors

Look for:
- 404 errors (files not found)
- JavaScript syntax errors
- CORS errors
- Network errors

## 📊 Performance Checks

### Load Time

- Target: < 2 seconds initial load
- Check: Network tab in DevTools
- Look for: Large file sizes, slow requests

### Runtime Performance

- Target: 60fps animations
- Check: Performance tab in DevTools
- Look for: Long tasks, layout thrashing

### Memory Usage

- Target: Stable memory over time
- Check: Memory tab in DevTools
- Look for: Memory leaks, growing heap

## ✅ Test Checklist

### Functionality
- [ ] Chat interface loads
- [ ] Messages appear correctly
- [ ] Search works
- [ ] Export downloads JSON
- [ ] Clear works with confirmation
- [ ] Text input sends commands
- [ ] Audio visualizer shows states
- [ ] Theme toggles smoothly
- [ ] Configuration persists

### Accessibility
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] Screen reader announces changes
- [ ] Skip links function
- [ ] Keyboard shortcuts work
- [ ] Color contrast sufficient
- [ ] Touch targets large enough (44px)

### Compatibility
- [ ] Chrome/Edge works
- [ ] Firefox works
- [ ] Safari works (if available)
- [ ] Mobile browsers work

## 📝 Test Results Template

```
Date: ___________
Tester: ___________
Browser: ___________

Functionality Tests:
[ ] Chat Interface
[ ] Audio Visualizer
[ ] Search/Filter
[ ] Export
[ ] Theme Switching
[ ] Configuration

Accessibility Tests:
[ ] Keyboard Navigation
[ ] Screen Reader
[ ] Color Contrast
[ ] Touch Targets

Issues Found:
1.
2.
3.

Overall Rating: ⭐⭐⭐⭐⭐
Comments:
```

## 🎯 Success Criteria

✅ **All Tests Pass**
✅ **No Console Errors**
✅ **Smooth Performance (60fps)**
✅ **Accessible with Keyboard**
✅ **Works in All Browsers**
✅ **Mobile Friendly**

## 📞 Support

If you encounter issues:
1. Check browser console
2. Review error messages
3. Verify all files loaded
4. Test in different browser
5. Check FRONTEND_REFACTORING_README.md

## 🚀 Next Steps After Testing

1. ✅ Fix any critical bugs
2. ✅ Implement missing backend endpoints
3. ✅ Connect real audio stream
4. ✅ Perform accessibility audit
5. ✅ Optimize performance
6. ✅ Document any changes
7. ✅ Plan Phase 6 enhancements

---

**Happy Testing! 🎉**
