const { createApp, ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } = Vue;

// Helper functions for showing messages
const showMessage = {
    success: (msg) => {
        if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
            ElementPlus.ElMessage.success(msg);
        } else {
            console.log('[Success]', msg);
        }
    },
    error: (msg) => {
        if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
            ElementPlus.ElMessage.error(msg);
        } else {
            console.error('[Error]', msg);
        }
    },
    warning: (msg) => {
        if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
            ElementPlus.ElMessage.warning(msg);
        } else {
            console.warn('[Warning]', msg);
        }
    }
};

// Element Plus default button colors
const BUTTON_COLORS = [
    { name: 'Primary', color: '#409eff' },
    { name: 'Success', color: '#67c23a' },
    { name: 'Warning', color: '#e6a23c' },
    { name: 'Danger', color: '#f56c6c' },
    { name: 'Info', color: '#909399' }
];

const app = createApp({
    setup() {
        const socket = io();
        const canvasRef = ref(null);
        const buttonsData = ref([]);
        const isEditing = ref(false);
        const mode = ref('custom_keys');
        const modifierKeys = ref([]);
        const specialKeys = ref([]);
        
        // Canvas state
        let ctx = null;
        let canvasWidth = 0;
        let canvasHeight = 0;
        let animationFrameId = null;
        
        // Edit dialog state
        const showEditDialog = ref(false);
        const editingButton = reactive({
            id: '',
            label: '',
            keys: [],
            colorIndex: 0,
            width: 100,
            height: 100,
            x: 10,
            y: 10
        });
        const selectedModifiers = ref([]); // Support multiple modifiers
        const selectedSpecialKey = ref('');
        const customKeyInput = ref('');
        
        // Driving mode state
        const showMainDeviceDialog = ref(false);
        const hasExistingMainDevice = ref(false);
        const isMainDevice = ref(false);
        const gyroData = reactive({ alpha: 0, beta: 0, gamma: 0 });
        
        // Responsive dialog width
        const dialogWidth = computed(() => {
            if (typeof window !== 'undefined' && window.innerWidth < 500) {
                return '95%';
            }
            return '500px';
        });
        
        // Track active buttons (currently pressed) - supports multiple simultaneous presses
        const activeButtonsMap = reactive({});
        
        // Pointer tracking for multi-touch support
        const pointerToButton = new Map(); // pointerId -> buttonId
        
        // Drag/resize state for edit mode
        let dragState = null; // { buttonIndex, mode: 'move'|'resize', offsetX, offsetY, corner }
        
        // Load initial config
        const loadConfig = async () => {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                buttonsData.value = data.buttons || [];
                mode.value = data.mode || 'custom_keys';
                modifierKeys.value = data.modifier_keys || ['ctrl', 'shift', 'alt', 'cmd', 'win'];
                specialKeys.value = data.special_keys || [];
                renderCanvas();
            } catch (error) {
                console.error('Failed to load config:', error);
            }
        };
        
        // Canvas rendering
        const initCanvas = () => {
            const canvas = canvasRef.value;
            if (!canvas) return;
            
            ctx = canvas.getContext('2d');
            resizeCanvas();
            
            window.addEventListener('resize', resizeCanvas);
            
            // Start render loop
            renderLoop();
        };
        
        const resizeCanvas = () => {
            const canvas = canvasRef.value;
            if (!canvas) return;
            
            const container = canvas.parentElement;
            const rect = container.getBoundingClientRect();
            
            // Use device pixel ratio for sharp rendering
            const dpr = window.devicePixelRatio || 1;
            canvasWidth = rect.width;
            canvasHeight = rect.height;
            
            canvas.width = canvasWidth * dpr;
            canvas.height = canvasHeight * dpr;
            canvas.style.width = canvasWidth + 'px';
            canvas.style.height = canvasHeight + 'px';
            
            ctx.scale(dpr, dpr);
            renderCanvas();
        };
        
        const renderLoop = () => {
            renderCanvas();
            animationFrameId = requestAnimationFrame(renderLoop);
        };
        
        const renderCanvas = () => {
            if (!ctx) return;
            
            // Clear canvas
            ctx.fillStyle = '#f0f2f5';
            ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // Draw each button
            buttonsData.value.forEach((btn, index) => {
                drawButton(btn, index);
            });
        };
        
        const drawButton = (btn, index) => {
            const isActive = !!activeButtonsMap[btn.id];
            const colorIndex = btn.colorIndex !== undefined ? btn.colorIndex : 0;
            const color = BUTTON_COLORS[colorIndex % BUTTON_COLORS.length].color;
            
            let x = btn.x;
            let y = btn.y;
            let width = btn.width;
            let height = btn.height;
            
            // Apply active press effect
            if (isActive) {
                const shrink = 3;
                x += shrink;
                y += shrink;
                width -= shrink * 2;
                height -= shrink * 2;
            }
            
            // Draw button background
            ctx.fillStyle = color;
            ctx.strokeStyle = isEditing.value ? '#409eff' : 'rgba(0,0,0,0.2)';
            ctx.lineWidth = isEditing.value ? 2 : 1;
            
            // Rounded rectangle
            const radius = 8;
            ctx.beginPath();
            ctx.moveTo(x + radius, y);
            ctx.lineTo(x + width - radius, y);
            ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
            ctx.lineTo(x + width, y + height - radius);
            ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
            ctx.lineTo(x + radius, y + height);
            ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
            ctx.lineTo(x, y + radius);
            ctx.quadraticCurveTo(x, y, x + radius, y);
            ctx.closePath();
            
            ctx.fill();
            
            if (isEditing.value) {
                ctx.setLineDash([5, 3]);
            }
            ctx.stroke();
            ctx.setLineDash([]);
            
            // Draw button label
            ctx.fillStyle = 'white';
            ctx.font = '600 14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.shadowColor = 'rgba(0,0,0,0.3)';
            ctx.shadowBlur = 2;
            ctx.shadowOffsetY = 1;
            ctx.fillText(btn.label, x + width/2, y + height/2);
            ctx.shadowBlur = 0;
            
            // Draw resize handle in edit mode
            if (isEditing.value) {
                const handleSize = 12;
                ctx.fillStyle = '#409eff';
                ctx.fillRect(
                    btn.x + btn.width - handleSize,
                    btn.y + btn.height - handleSize,
                    handleSize,
                    handleSize
                );
            }
        };
        
        // Find button at a given point (canvas coordinates)
        const getButtonAtPoint = (canvasX, canvasY) => {
            // Check buttons in reverse order (top-most first)
            for (let i = buttonsData.value.length - 1; i >= 0; i--) {
                const btn = buttonsData.value[i];
                if (canvasX >= btn.x && canvasX <= btn.x + btn.width &&
                    canvasY >= btn.y && canvasY <= btn.y + btn.height) {
                    return { button: btn, index: i };
                }
            }
            return null;
        };
        
        // Check if point is on resize handle
        const isOnResizeHandle = (btn, canvasX, canvasY) => {
            const handleSize = 16;
            return canvasX >= btn.x + btn.width - handleSize &&
                   canvasX <= btn.x + btn.width &&
                   canvasY >= btn.y + btn.height - handleSize &&
                   canvasY <= btn.y + btn.height;
        };
        
        // Convert page coordinates to canvas coordinates
        const pageToCanvas = (pageX, pageY) => {
            const canvas = canvasRef.value;
            if (!canvas) return { x: 0, y: 0 };
            const rect = canvas.getBoundingClientRect();
            return {
                x: pageX - rect.left,
                y: pageY - rect.top
            };
        };
        
        // Handle button press
        const handleButtonPress = (btnId) => {
            const btn = buttonsData.value.find(b => b.id === btnId);
            if (!btn) return;
            
            activeButtonsMap[btnId] = true;
            socket.emit('button_down', { id: btn.id, label: btn.label, keys: btn.keys });
        };
        
        // Handle button release
        const handleButtonRelease = (btnId) => {
            if (!activeButtonsMap[btnId]) return;
            
            delete activeButtonsMap[btnId];
            socket.emit('button_up', { id: btnId });
        };
        
        // Canvas event handlers
        const setupCanvasEvents = () => {
            const canvas = canvasRef.value;
            if (!canvas) return;
            
            canvas.addEventListener('pointerdown', onCanvasPointerDown, { passive: false });
            canvas.addEventListener('pointermove', onCanvasPointerMove, { passive: false });
            canvas.addEventListener('pointerup', onCanvasPointerUp, { passive: false });
            canvas.addEventListener('pointercancel', onCanvasPointerUp, { passive: false });
            canvas.addEventListener('pointerleave', onCanvasPointerUp, { passive: false });
        };
        
        const onCanvasPointerDown = (e) => {
            e.preventDefault();
            const canvas = canvasRef.value;
            canvas.setPointerCapture(e.pointerId);
            
            const { x, y } = pageToCanvas(e.clientX, e.clientY);
            const hit = getButtonAtPoint(x, y);
            
            if (!hit) return;
            
            if (isEditing.value) {
                // Check if on resize handle
                if (isOnResizeHandle(hit.button, x, y)) {
                    dragState = {
                        buttonIndex: hit.index,
                        mode: 'resize',
                        startWidth: hit.button.width,
                        startHeight: hit.button.height,
                        startX: x,
                        startY: y
                    };
                } else {
                    dragState = {
                        buttonIndex: hit.index,
                        mode: 'move',
                        offsetX: x - hit.button.x,
                        offsetY: y - hit.button.y
                    };
                }
            } else {
                // Normal mode - track button press
                pointerToButton.set(e.pointerId, hit.button.id);
                handleButtonPress(hit.button.id);
            }
        };
        
        const onCanvasPointerMove = (e) => {
            e.preventDefault();
            const { x, y } = pageToCanvas(e.clientX, e.clientY);
            
            if (isEditing.value && dragState) {
                const btn = buttonsData.value[dragState.buttonIndex];
                
                if (dragState.mode === 'move') {
                    btn.x = Math.max(0, Math.min(x - dragState.offsetX, canvasWidth - btn.width));
                    btn.y = Math.max(0, Math.min(y - dragState.offsetY, canvasHeight - btn.height));
                } else if (dragState.mode === 'resize') {
                    const deltaX = x - dragState.startX;
                    const deltaY = y - dragState.startY;
                    btn.width = Math.max(50, Math.min(300, dragState.startWidth + deltaX));
                    btn.height = Math.max(50, Math.min(300, dragState.startHeight + deltaY));
                }
            } else if (!isEditing.value) {
                // Check if pointer moved to different button
                const currentBtnId = pointerToButton.get(e.pointerId);
                if (currentBtnId === undefined) return;
                
                const hit = getButtonAtPoint(x, y);
                const newBtnId = hit ? hit.button.id : null;
                
                if (newBtnId !== currentBtnId) {
                    // Release old button
                    if (currentBtnId) {
                        handleButtonRelease(currentBtnId);
                    }
                    // Press new button
                    if (newBtnId) {
                        pointerToButton.set(e.pointerId, newBtnId);
                        handleButtonPress(newBtnId);
                    } else {
                        pointerToButton.delete(e.pointerId);
                    }
                }
            }
        };
        
        const onCanvasPointerUp = (e) => {
            e.preventDefault();
            
            if (isEditing.value) {
                dragState = null;
            } else {
                const btnId = pointerToButton.get(e.pointerId);
                if (btnId) {
                    handleButtonRelease(btnId);
                    pointerToButton.delete(e.pointerId);
                }
            }
        };
        
        // Double-click to edit button
        const onCanvasDoubleClick = (e) => {
            if (!isEditing.value) return;
            
            const { x, y } = pageToCanvas(e.clientX, e.clientY);
            const hit = getButtonAtPoint(x, y);
            
            if (hit) {
                editButton(hit.button);
            }
        };
        
        // Edit mode functions
        const toggleEditMode = () => {
            isEditing.value = !isEditing.value;
            // Clear active buttons when entering edit mode
            if (isEditing.value) {
                Object.keys(activeButtonsMap).forEach(btnId => {
                    handleButtonRelease(btnId);
                });
                pointerToButton.clear();
            }
        };
        
        const saveLayout = () => {
            socket.emit('save_layout', buttonsData.value);
        };
        
        const editButton = (btn) => {
            if (!isEditing.value) return;
            
            Object.assign(editingButton, {
                id: btn.id,
                label: btn.label,
                keys: [...(btn.keys || [])],
                colorIndex: btn.colorIndex !== undefined ? btn.colorIndex : 0,
                width: btn.width || 100,
                height: btn.height || 100,
                x: btn.x,
                y: btn.y
            });
            showEditDialog.value = true;
        };
        
        const addNewButton = () => {
            Object.assign(editingButton, {
                id: '',
                label: 'New',
                keys: [],
                colorIndex: 0,
                width: 80,
                height: 80,
                x: 50,
                y: 50
            });
            showEditDialog.value = true;
        };
        
        // Add all selected keys at once (supports multiple modifiers)
        const addKey = () => {
            // Add all selected modifiers
            selectedModifiers.value.forEach(mod => {
                if (!editingButton.keys.includes(mod)) {
                    editingButton.keys.push(mod);
                }
            });
            selectedModifiers.value = [];
            
            // Add special key
            if (selectedSpecialKey.value) {
                if (!editingButton.keys.includes(selectedSpecialKey.value)) {
                    editingButton.keys.push(selectedSpecialKey.value);
                }
                selectedSpecialKey.value = '';
            }
            
            // Add custom key
            if (customKeyInput.value) {
                const key = customKeyInput.value.toLowerCase();
                if (!editingButton.keys.includes(key)) {
                    editingButton.keys.push(key);
                }
                customKeyInput.value = '';
            }
        };
        
        const removeKey = (index) => {
            editingButton.keys.splice(index, 1);
        };
        
        const saveButtonEdit = async () => {
            const buttonData = {
                id: editingButton.id,
                label: editingButton.label,
                keys: editingButton.keys,
                colorIndex: editingButton.colorIndex,
                width: editingButton.width,
                height: editingButton.height,
                x: editingButton.x,
                y: editingButton.y
            };
            
            try {
                if (editingButton.id) {
                    // Update existing button
                    await fetch('/api/update_button', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(buttonData)
                    });
                    
                    // Update local data
                    const index = buttonsData.value.findIndex(b => b.id === editingButton.id);
                    if (index >= 0) {
                        buttonsData.value[index] = { ...buttonData };
                    }
                } else {
                    // Add new button
                    const response = await fetch('/api/add_button', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(buttonData)
                    });
                    const result = await response.json();
                    buttonData.id = result.id;
                    buttonsData.value.push(buttonData);
                }
                
                showEditDialog.value = false;
            } catch (error) {
                console.error('Failed to save button:', error);
                showMessage.error('Failed to save button');
            }
        };
        
        const deleteButton = async () => {
            if (!editingButton.id) return;
            
            try {
                await fetch('/api/delete_button', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: editingButton.id })
                });
                
                buttonsData.value = buttonsData.value.filter(b => b.id !== editingButton.id);
                showEditDialog.value = false;
            } catch (error) {
                console.error('Failed to delete button:', error);
                showMessage.error('Failed to delete button');
            }
        };
        
        // Driving mode functions
        const setAsMainDevice = (isMain) => {
            socket.emit('set_main_device', { is_main: isMain });
            showMainDeviceDialog.value = false;
        };
        
        // Gyroscope handling
        const startGyroscope = () => {
            if (typeof DeviceOrientationEvent !== 'undefined') {
                if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                    DeviceOrientationEvent.requestPermission()
                        .then(permissionState => {
                            if (permissionState === 'granted') {
                                window.addEventListener('deviceorientation', handleGyro);
                            }
                        })
                        .catch(console.error);
                } else {
                    window.addEventListener('deviceorientation', handleGyro);
                }
            }
        };
        
        const stopGyroscope = () => {
            window.removeEventListener('deviceorientation', handleGyro);
        };
        
        const handleGyro = (event) => {
            gyroData.alpha = event.alpha || 0;
            gyroData.beta = event.beta || 0;
            gyroData.gamma = event.gamma || 0;
            
            socket.emit('gyro_data', {
                alpha: gyroData.alpha,
                beta: gyroData.beta,
                gamma: gyroData.gamma
            });
        };
        
        // Socket event handlers
        socket.on('ask_main_device', (data) => {
            hasExistingMainDevice.value = data.current_main;
            showMainDeviceDialog.value = true;
        });
        
        socket.on('main_status_changed', (data) => {
            isMainDevice.value = data.is_main;
            if (data.is_main) {
                startGyroscope();
            } else {
                stopGyroscope();
            }
        });
        
        socket.on('layout_saved', (data) => {
            showMessage.success('Layout Saved!');
            isEditing.value = false;
        });
        
        // Lifecycle
        onMounted(() => {
            loadConfig();
            nextTick(() => {
                initCanvas();
                setupCanvasEvents();
                
                // Setup double-click
                const canvas = canvasRef.value;
                if (canvas) {
                    canvas.addEventListener('dblclick', onCanvasDoubleClick);
                }
            });
        });
        
        onUnmounted(() => {
            stopGyroscope();
            if (animationFrameId) {
                cancelAnimationFrame(animationFrameId);
            }
            window.removeEventListener('resize', resizeCanvas);
        });
        
        return {
            canvasRef,
            buttonsData,
            isEditing,
            mode,
            modifierKeys,
            specialKeys,
            showEditDialog,
            editingButton,
            selectedModifiers,
            selectedSpecialKey,
            customKeyInput,
            showMainDeviceDialog,
            hasExistingMainDevice,
            isMainDevice,
            gyroData,
            dialogWidth,
            activeButtonsMap,
            BUTTON_COLORS,
            toggleEditMode,
            saveLayout,
            editButton,
            addNewButton,
            addKey,
            removeKey,
            saveButtonEdit,
            deleteButton,
            setAsMainDevice
        };
    }
});

app.use(ElementPlus);
app.mount('#app');
