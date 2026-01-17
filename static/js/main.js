const { createApp, ref, reactive, onMounted, onUnmounted, nextTick } = Vue;

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

const app = createApp({
    setup() {
        const socket = io();
        const gamePad = ref(null);
        const buttonsData = ref([]);
        const isEditing = ref(false);
        const mode = ref('custom_keys');
        const modifierKeys = ref([]);
        const specialKeys = ref([]);
        
        // Edit dialog state
        const showEditDialog = ref(false);
        const editingButton = reactive({
            id: '',
            label: '',
            keys: [],
            color: '#555555',
            width: 100,
            height: 100,
            x: 10,
            y: 10
        });
        const selectedModifier = ref('');
        const selectedSpecialKey = ref('');
        const customKeyInput = ref('');
        
        // Driving mode state
        const showMainDeviceDialog = ref(false);
        const hasExistingMainDevice = ref(false);
        const isMainDevice = ref(false);
        const gyroData = reactive({ alpha: 0, beta: 0, gamma: 0 });
        
        // Track active buttons (currently pressed) - use reactive object
        const activeButtonsMap = reactive({});
        const activeButtons = {
            has(id) { return !!activeButtonsMap[id]; },
            add(id) { activeButtonsMap[id] = true; },
            delete(id) { delete activeButtonsMap[id]; },
            clear() { Object.keys(activeButtonsMap).forEach(k => delete activeButtonsMap[k]); }
        };
        
        // Drag state
        let draggedButton = null;
        let dragOffset = { x: 0, y: 0 };
        
        // Touch tracking for proper button detection
        let activeTouches = new Map(); // touchId -> buttonId
        
        // Load initial config
        const loadConfig = async () => {
            try {
                const response = await fetch('/api/config');
                const data = await response.json();
                buttonsData.value = data.buttons || [];
                mode.value = data.mode || 'custom_keys';
                modifierKeys.value = data.modifier_keys || ['ctrl', 'shift', 'alt', 'cmd', 'win'];
                specialKeys.value = data.special_keys || [];
            } catch (error) {
                console.error('Failed to load config:', error);
            }
        };
        
        // Find button element at a given point
        const getButtonAtPoint = (x, y) => {
            const elements = document.elementsFromPoint(x, y);
            for (const el of elements) {
                if (el.classList.contains('game-btn')) {
                    return el;
                }
            }
            return null;
        };
        
        // Get button data by ID
        const getButtonData = (id) => {
            return buttonsData.value.find(btn => btn.id === id);
        };
        
        // Handle button press
        const handleButtonPress = (btnId, element) => {
            const btn = getButtonData(btnId);
            if (!btn) return;
            
            activeButtons.add(btnId);
            socket.emit('button_down', { id: btn.id, label: btn.label });
        };
        
        // Handle button release
        const handleButtonRelease = (btnId) => {
            const btn = getButtonData(btnId);
            if (!btn) return;
            
            activeButtons.delete(btnId);
            socket.emit('button_up', { id: btn.id });
        };
        
        // Setup touch/pointer event handlers after Vue renders
        const setupEventHandlers = () => {
            const pad = gamePad.value;
            if (!pad) return;
            
            // Use pointer events for unified touch/mouse handling
            pad.addEventListener('pointerdown', onPointerDown, { passive: false });
            pad.addEventListener('pointermove', onPointerMove, { passive: false });
            pad.addEventListener('pointerup', onPointerUp, { passive: false });
            pad.addEventListener('pointercancel', onPointerUp, { passive: false });
            pad.addEventListener('pointerleave', onPointerUp, { passive: false });
        };
        
        const onPointerDown = (e) => {
            e.preventDefault();
            
            const buttonEl = getButtonAtPoint(e.clientX, e.clientY);
            if (!buttonEl) return;
            
            const btnId = buttonEl.dataset.id;
            
            if (isEditing.value) {
                // Start dragging in edit mode
                startDrag(e, buttonEl);
            } else {
                // Track this touch/pointer
                activeTouches.set(e.pointerId, btnId);
                handleButtonPress(btnId, buttonEl);
            }
        };
        
        const onPointerMove = (e) => {
            e.preventDefault();
            
            if (isEditing.value && draggedButton) {
                // Handle drag movement
                moveDrag(e);
            } else if (!isEditing.value) {
                // Check if pointer moved to a different button
                const currentBtnId = activeTouches.get(e.pointerId);
                if (currentBtnId === undefined) return;
                
                const buttonEl = getButtonAtPoint(e.clientX, e.clientY);
                const newBtnId = buttonEl ? buttonEl.dataset.id : null;
                
                if (newBtnId !== currentBtnId) {
                    // Pointer moved to different button
                    if (currentBtnId) {
                        handleButtonRelease(currentBtnId);
                    }
                    if (newBtnId) {
                        activeTouches.set(e.pointerId, newBtnId);
                        handleButtonPress(newBtnId, buttonEl);
                    } else {
                        activeTouches.delete(e.pointerId);
                    }
                }
            }
        };
        
        const onPointerUp = (e) => {
            e.preventDefault();
            
            if (isEditing.value) {
                endDrag();
            } else {
                const btnId = activeTouches.get(e.pointerId);
                if (btnId) {
                    handleButtonRelease(btnId);
                    activeTouches.delete(e.pointerId);
                }
            }
        };
        
        // Drag functions for edit mode
        const startDrag = (e, el) => {
            draggedButton = el;
            const rect = el.getBoundingClientRect();
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            el.setPointerCapture(e.pointerId);
        };
        
        const moveDrag = (e) => {
            if (!draggedButton) return;
            
            const pad = gamePad.value;
            const padRect = pad.getBoundingClientRect();
            
            let newX = e.clientX - padRect.left - dragOffset.x;
            let newY = e.clientY - padRect.top - dragOffset.y;
            
            // Clamp to boundaries
            newX = Math.max(0, Math.min(newX, padRect.width - draggedButton.offsetWidth));
            newY = Math.max(0, Math.min(newY, padRect.height - draggedButton.offsetHeight));
            
            draggedButton.style.left = newX + 'px';
            draggedButton.style.top = newY + 'px';
            
            // Update data model
            const index = parseInt(draggedButton.dataset.index);
            buttonsData.value[index].x = newX;
            buttonsData.value[index].y = newY;
        };
        
        const endDrag = () => {
            draggedButton = null;
        };
        
        // Edit mode functions
        const toggleEditMode = () => {
            isEditing.value = !isEditing.value;
            // Clear active buttons when entering edit mode
            if (isEditing.value) {
                Object.keys(activeButtonsMap).forEach(btnId => {
                    handleButtonRelease(btnId);
                });
                activeButtons.clear();
                activeTouches.clear();
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
                color: btn.color || '#555555',
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
                label: 'New Button',
                keys: [],
                color: '#555555',
                width: 100,
                height: 100,
                x: 50,
                y: 50
            });
            showEditDialog.value = true;
        };
        
        const addKey = () => {
            let keyToAdd = '';
            
            if (selectedModifier.value) {
                keyToAdd = selectedModifier.value;
                editingButton.keys.push(keyToAdd);
                selectedModifier.value = '';
            }
            
            if (selectedSpecialKey.value) {
                keyToAdd = selectedSpecialKey.value;
                editingButton.keys.push(keyToAdd);
                selectedSpecialKey.value = '';
            }
            
            if (customKeyInput.value) {
                keyToAdd = customKeyInput.value.toLowerCase();
                editingButton.keys.push(keyToAdd);
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
                color: editingButton.color,
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
        let gyroHandler = null;
        
        const startGyroscope = () => {
            if (typeof DeviceOrientationEvent !== 'undefined') {
                // Check if we need to request permission (iOS 13+)
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
                setupEventHandlers();
            });
        });
        
        onUnmounted(() => {
            stopGyroscope();
        });
        
        return {
            gamePad,
            buttonsData,
            isEditing,
            mode,
            modifierKeys,
            specialKeys,
            showEditDialog,
            editingButton,
            selectedModifier,
            selectedSpecialKey,
            customKeyInput,
            showMainDeviceDialog,
            hasExistingMainDevice,
            isMainDevice,
            gyroData,
            activeButtons,
            activeButtonsMap,
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
