const {
    createApp,
    ref,
    reactive,
    computed,
    onMounted,
    onUnmounted,
    nextTick,
    watch
} = Vue;

// Constants
const MIN_BUTTON_SIZE = 50;
const MAX_BUTTON_SIZE = 200;
const BUTTON_EVENT_DELAY = 0; // Delay in ms between button_down and button_up events

// 用于显示消息的辅助函数
const showMessage = {
    success: (msg) => {
        if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
            ElementPlus.ElMessage.success(msg);
        } else {
            console.log('[成功]', msg);
        }
    },
    error: (msg) => {
        if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
            ElementPlus.ElMessage.error(msg);
        } else {
            console.error('[错误]', msg);
        }
    },
    warning: (msg) => {
        if (typeof ElementPlus !== 'undefined' && ElementPlus.ElMessage) {
            ElementPlus.ElMessage.warning(msg);
        } else {
            console.warn('[警告]', msg);
        }
    }
};

// Element Plus 默认按钮配色
const BUTTON_COLORS = [
    { name: '主色', color: '#409eff' },
    { name: '成功', color: '#67c23a' },
    { name: '警告', color: '#e6a23c' },
    { name: '危险', color: '#f56c6c' },
    { name: '信息', color: '#909399' }
];

const app = createApp({
    setup() {
        const socket = io();
        const canvasRef = ref(null);
        const buttonsData = ref([]);
        const slidersData = ref([]);  // 拖动条数据
        const isEditing = ref(false);
        const mode = ref('custom_keys');
        const modifierKeys = ref([]);
        const specialKeys = ref([]);
        
        // 驾驶模式配置
        const drivingConfig = reactive({
            gyro_sensitivity: 1.0,
            gyro_deadzone: 2.0,
            max_steering_angle: 45.0,
            gyro_update_rate: 60,
            // 旧的陀螺仪轴映射（保留用于兼容性）
            gyro_axis_mapping: {
                gamma: 'left_x',
                beta: 'left_y',
                alpha: null
            },
            sliders: [],
            // 新的统一轴配置
            axis_config: {
                left_x: { source_type: 'none', source_id: null, peak_value: 1.0, deadzone: 0.05, gyro_range: 90.0 },
                left_y: { source_type: 'none', source_id: null, peak_value: 1.0, deadzone: 0.05, gyro_range: 90.0 },
                right_x: { source_type: 'none', source_id: null, peak_value: 1.0, deadzone: 0.05, gyro_range: 90.0 },
                right_y: { source_type: 'none', source_id: null, peak_value: 1.0, deadzone: 0.05, gyro_range: 90.0 },
                left_trigger: { source_type: 'none', source_id: null, peak_value: 1.0, deadzone: 0.05, gyro_range: 90.0 },
                right_trigger: { source_type: 'none', source_id: null, peak_value: 1.0, deadzone: 0.05, gyro_range: 90.0 }
            }
        });
        
        // 摇杆类型和自定义摇杆配置
        const joystickType = ref('xbox360');  // 'xbox360' 或 'custom'
        const customJoystickAxisCount = ref(8);  // 自定义摇杆的轴数量
        const customAxisMapping = reactive({});  // 自定义摇杆的轴映射
        
        // 初始化自定义摇杆轴映射（确保所有轴都有配置）
        const initializeCustomAxisMapping = () => {
            for (let i = 0; i < customJoystickAxisCount.value; i++) {
                if (!customAxisMapping[i]) {
                    customAxisMapping[i] = {
                        source_type: 'none',
                        source_id: null,
                        peak_value: 1.0,
                        deadzone: 0.05,
                        gyro_range: 90.0,
                        invert: false
                    };
                }
            }
        };
        
        // 监听轴数量变化，自动初始化新的轴配置
        watch(customJoystickAxisCount, () => {
            initializeCustomAxisMapping();
        });
        
        // Canvas state
        let ctx = null;
        let canvasWidth = 0;
        let canvasHeight = 0;
        let animationFrameId = null;
        
        // 跟踪pointer事件序列中是否碰到了操控组件
        const pointerTouchedControl = new Map();
        
        // 编辑对话态
        const showEditDialog = ref(false);
        const showDrivingConfigDialog = ref(false);  // 驾驶模式配置对话框
        const editingButton = reactive({
            id: '',
            type: 'button',  // 'button' 或 'slider'
            label: '',
            keys: [],
            colorIndex: 0,
            width: 100,
            height: 100,
            x: 10,
            y: 10,
            // 拖动条特有属性
            orientation: 'horizontal',  // 'horizontal' 或 'vertical'
            autoCenter: true,  // 是否自动归中
            axis: 'right_x',  // 绑定的xbox轴
            rangeMode: 'bipolar'  // 'bipolar' ([-1, 1]) 或 'unipolar' ([0, 1])
        });
        const selectedModifiers = ref([]); // 支持多个修饰键
        const selectedSpecialKey = ref('');
        const customKeyInput = ref('');
        
        // 驾驶模式状态
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
        
        // 获取可用于特定轴的滑块列表（排除已绑定到其他轴的滑块）
        const getAvailableSlidersForAxis = (currentAxis) => {
            const sliders = buttonsData.value.filter(b => b.type === 'slider');
            const currentSourceId = drivingConfig.axis_config[currentAxis]?.source_id;
            
            return sliders.map(slider => {
                // 检查此滑块是否已绑定到其他轴
                const boundToOtherAxis = Object.entries(drivingConfig.axis_config || {}).some(
                    ([axis, cfg]) => axis !== currentAxis && cfg.source_type === 'slider' && cfg.source_id === slider.id
                );
                
                return {
                    id: slider.id,
                    label: slider.label,
                    isBound: boundToOtherAxis,
                    displayLabel: boundToOtherAxis ? `${slider.label} [已绑定到其他轴]` : slider.label,
                    disabled: boundToOtherAxis
                };
            });
        };
        
        // 轴配置列表（用于表格显示）
        const axisConfigList = computed(() => {
            const axes = ['left_x', 'left_y', 'right_x', 'right_y', 'left_trigger', 'right_trigger'];
            return axes.map(axisName => {
                // 直接返回 drivingConfig.axis_config[axisName] 的引用
                // 这样在表格中修改 scope.row 的属性会直接反映到 drivingConfig 中
                const cfg = drivingConfig.axis_config[axisName];
                cfg.axis = axisName; // 确保包含 axis 属性供前端显示逻辑使用
                return cfg;
            });
        });
        
        // 自定义摇杆轴配置列表
        const customAxisConfigList = computed(() => {
            const list = [];
            for (let i = 0; i < customJoystickAxisCount.value; i++) {
                const cfg = customAxisMapping[i];
                if (cfg) {
                    // 创建一个新对象，包含 axisIndex，而不是直接修改 cfg
                    list.push({
                        ...cfg,
                        axisIndex: i
                    });
                }
            }
            return list;
        });
        
        // 获取轴的显示名称
        const getAxisDisplayName = (axis) => {
            const names = {
                'left_x': '左摇杆 X',
                'left_y': '左摇杆 Y',
                'right_x': '右摇杆 X',
                'right_y': '右摇杆 Y',
                'left_trigger': '左扳机',
                'right_trigger': '右扳机'
            };
            return names[axis] || axis;
        };
        
        // 当轴的源类型改变时
        const onAxisSourceTypeChange = (axisConfig) => {
            if (axisConfig.source_type === 'none') {
                axisConfig.source_id = null;
            }
        };
        
        // 当自定义轴的源类型改变时
        const onCustomAxisSourceTypeChange = (axisConfig) => {
            if (axisConfig.source_type === 'none') {
                axisConfig.source_id = null;
            }
        };
        
        // 当摇杆类型改变时
        const onJoystickTypeChange = () => {
            console.log('摇杆类型改变为:', joystickType.value);
        };
        
        // 当自定义摇杆轴数量改变时
        const onCustomAxisCountChange = () => {
            console.log('自定义摇杆轴数量改变为:', customJoystickAxisCount.value);
        };
        
        // 获取自定义轴可用的拖动条（排除已被其他轴绑定的拖动条）
        const getAvailableSlidersForCustomAxis = (currentAxisIndex) => {
            const sliders = buttonsData.value.filter(b => b.type === 'slider');
            
            // 找出已被其他轴绑定的拖动条
            const boundSliders = new Set();
            for (let i = 0; i < customJoystickAxisCount.value; i++) {
                if (i !== currentAxisIndex && customAxisMapping[i]?.source_type === 'slider') {
                    boundSliders.add(customAxisMapping[i].source_id);
                }
            }
            
            return sliders.map(slider => ({
                id: slider.id,
                displayLabel: slider.label || slider.id,
                disabled: boundSliders.has(slider.id)
            }));
        };
        
        // Helper function to get default value based on range mode
        const getSliderDefaultValue = (rangeMode) => {
            return rangeMode === 'unipolar' ? 0.5 : 0.0;
        };
        
        // Track active buttons (currently pressed) - supports multiple simultaneous presses
        const activeButtonsMap = reactive({});
        
        // Pointer tracking for multi-touch support
        const pointerToButton = new Map(); // pointerId -> buttonId
        
        // Timeout tracking for button event delays
        const pendingButtonTimeouts = new Set();
        
        // 编辑模式下的拖拽/缩放状态
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
                
                // 清理旧的 axis 属性从所有滑块中
                buttonsData.value.forEach(btn => {
                    if (btn.type === 'slider' && btn.hasOwnProperty('axis')) {
                        delete btn.axis;
                    }
                });
                
                // 加载摇杆类型和自定义摇杆配置
                if (data.joystick_type) {
                    joystickType.value = data.joystick_type;
                }
                
                if (data.custom_joystick) {
                    customJoystickAxisCount.value = data.custom_joystick.axis_count || 8;
                    if (data.custom_joystick.axis_mapping) {
                        Object.assign(customAxisMapping, data.custom_joystick.axis_mapping);
                    }
                    // 初始化任何缺失的轴配置
                    initializeCustomAxisMapping();
                }
                
                // 加载驾驶模式配置
                if (data.driving_config) {
                    Object.assign(drivingConfig, data.driving_config);
                    slidersData.value = drivingConfig.sliders || [];
                    
                    // 如果没有新的轴配置，从旧的gyro_axis_mapping和slider配置迁移
                    if (!drivingConfig.axis_config || Object.keys(drivingConfig.axis_config).length === 0) {
                        migrateToUnifiedAxisConfig();
                    } else {
                        // 确保所有轴都有配置
                        const axes = ['left_x', 'left_y', 'right_x', 'right_y', 'left_trigger', 'right_trigger'];
                        axes.forEach(axis => {
                            if (!drivingConfig.axis_config[axis]) {
                                drivingConfig.axis_config[axis] = {
                                    source_type: 'none',
                                    source_id: null,
                                    peak_value: 1.0,
                                    deadzone: 0.05,
                                    gyro_range: 90.0
                                };
                            } else if (drivingConfig.axis_config[axis].gyro_range === undefined) {
                                // 为已存在的配置添加 gyro_range 字段
                                drivingConfig.axis_config[axis].gyro_range = 90.0;
                            }
                        });
                    }
                }
                
                markDirty();
            } catch (error) {
                console.error('加载配置失败：', error);
            }
        };
        
        // 从旧配置迁移到新的统一轴配置
        const migrateToUnifiedAxisConfig = () => {
            console.log('[迁移] 从旧配置迁移到统一轴配置');
            
            // 初始化轴配置
            const axes = ['left_x', 'left_y', 'right_x', 'right_y', 'left_trigger', 'right_trigger'];
            axes.forEach(axis => {
                drivingConfig.axis_config[axis] = {
                    source_type: 'none',
                    source_id: null,
                    peak_value: 1.0,
                    deadzone: 0.05,
                    gyro_range: 90.0
                };
            });
            
            // 从旧的 gyro_axis_mapping 迁移
            if (drivingConfig.gyro_axis_mapping) {
                Object.entries(drivingConfig.gyro_axis_mapping).forEach(([gyroAxis, gamepadAxis]) => {
                    if (gamepadAxis && drivingConfig.axis_config[gamepadAxis]) {
                        drivingConfig.axis_config[gamepadAxis].source_type = 'gyro';
                        drivingConfig.axis_config[gamepadAxis].source_id = gyroAxis;
                    }
                });
            }
            
            // 从旧的 sliders 配置迁移
            if (drivingConfig.sliders && drivingConfig.sliders.length > 0) {
                drivingConfig.sliders.forEach(slider => {
                    if (slider.axis && drivingConfig.axis_config[slider.axis]) {
                        drivingConfig.axis_config[slider.axis].source_type = 'slider';
                        drivingConfig.axis_config[slider.axis].source_id = slider.id;
                    }
                });
            }
            
            console.log('[迁移] 迁移完成', drivingConfig.axis_config);
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
            needsRender = true;
        };
        
        // Dirty flag for optimized rendering
        let needsRender = true;
        
        const markDirty = () => {
            needsRender = true;
        };
        
        const renderLoop = () => {
            if (needsRender) {
                renderCanvas();
                needsRender = false;
            }
            animationFrameId = requestAnimationFrame(renderLoop);
        };
        
        const renderCanvas = () => {
            if (!ctx) return;
            
            // Clear canvas
            ctx.fillStyle = '#f0f2f5';
            ctx.fillRect(0, 0, canvasWidth, canvasHeight);
            
            // Draw each button
            buttonsData.value.forEach((btn, index) => {
                if (btn.type === 'slider') {
                    drawSlider(btn, index);
                } else {
                    drawButton(btn, index);
                }
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
            
            // 在编辑模式下绘制缩放把手
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
        
        const drawSlider = (slider, index) => {
            const colorIndex = slider.colorIndex !== undefined ? slider.colorIndex : 0;
            const color = BUTTON_COLORS[colorIndex % BUTTON_COLORS.length].color;
            
            // 获取当前值和范围模式
            const rangeMode = slider.rangeMode || 'bipolar';  // 'bipolar' ([-1, 1]) 或 'unipolar' ([0, 1])
            const sliderValue = slider.currentValue !== undefined ? slider.currentValue : getSliderDefaultValue(rangeMode);
            
            // 绘制背景轨道
            ctx.fillStyle = 'rgba(0,0,0,0.1)';
            ctx.strokeStyle = isEditing.value ? '#409eff' : 'rgba(0,0,0,0.2)';
            ctx.lineWidth = isEditing.value ? 2 : 1;
            
            const radius = 8;
            ctx.beginPath();
            ctx.moveTo(slider.x + radius, slider.y);
            ctx.lineTo(slider.x + slider.width - radius, slider.y);
            ctx.quadraticCurveTo(slider.x + slider.width, slider.y, slider.x + slider.width, slider.y + radius);
            ctx.lineTo(slider.x + slider.width, slider.y + slider.height - radius);
            ctx.quadraticCurveTo(slider.x + slider.width, slider.y + slider.height, slider.x + slider.width - radius, slider.y + slider.height);
            ctx.lineTo(slider.x + radius, slider.y + slider.height);
            ctx.quadraticCurveTo(slider.x, slider.y + slider.height, slider.x, slider.y + slider.height - radius);
            ctx.lineTo(slider.x, slider.y + radius);
            ctx.quadraticCurveTo(slider.x, slider.y, slider.x + radius, slider.y);
            ctx.closePath();
            ctx.fill();
            
            if (isEditing.value) {
                ctx.setLineDash([5, 3]);
            }
            ctx.stroke();
            ctx.setLineDash([]);
            
            // 绘制滑块
            const knobSize = slider.orientation === 'horizontal' ? slider.height * 0.8 : slider.width * 0.8;
            let knobX, knobY;
            
            if (slider.orientation === 'horizontal') {
                // 横向拖动条
                const centerY = slider.y + slider.height / 2;
                const rangeX = slider.width - knobSize;
                
                // 根据范围模式计算位置
                let normalizedPos;
                if (rangeMode === 'unipolar') {
                    // unipolar: sliderValue 范围 [0, 1]，左侧为 0，右侧为 1
                    normalizedPos = sliderValue;
                } else {
                    // bipolar: sliderValue 范围 [-1, 1]，左侧为 -1，中心为 0，右侧为 1
                    normalizedPos = (sliderValue + 1.0) / 2.0;
                }
                
                knobX = slider.x + knobSize / 2 + normalizedPos * rangeX;
                knobY = centerY;
                
                // 绘制滑块
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(knobX, knobY, knobSize / 2, 0, Math.PI * 2);
                ctx.fill();
            } else {
                // 竖向拖动条
                const centerX = slider.x + slider.width / 2;
                const rangeY = slider.height - knobSize;
                
                // 根据范围模式计算位置
                let normalizedPos;
                if (rangeMode === 'unipolar') {
                    // unipolar: sliderValue 范围 [0, 1]，底部为 0，顶部为 1
                    normalizedPos = 1.0 - sliderValue;
                } else {
                    // bipolar: sliderValue 范围 [-1, 1]，底部为 -1，中心为 0，顶部为 1
                    normalizedPos = (1.0 - sliderValue) / 2.0;
                }
                
                knobX = centerX;
                knobY = slider.y + knobSize / 2 + normalizedPos * rangeY;
                
                // 绘制滑块
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(knobX, knobY, knobSize / 2, 0, Math.PI * 2);
                ctx.fill();
            }
            
            // \u7ed8\u5236\u6807\u7b7e
            ctx.fillStyle = 'rgba(0,0,0,0.7)';
            ctx.font = '600 12px -apple-system, BlinkMacSystemFont, \"Segoe UI\", Roboto, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillText(slider.label, slider.x + slider.width / 2, slider.y + 4);
            
            // \u5728\u7f16\u8f91\u6a21\u5f0f\u4e0b\u7ed8\u5236\u7f29\u653e\u628a\u624b
            if (isEditing.value) {
                const handleSize = 12;
                ctx.fillStyle = '#409eff';
                ctx.fillRect(
                    slider.x + slider.width - handleSize,
                    slider.y + slider.height - handleSize,
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
        
        // Handle button press (visual only, no key action)
        const handleButtonPress = (btnId) => {
            const btn = buttonsData.value.find(b => b.id === btnId);
            if (!btn) return;
            
            if (btn.type === 'slider') {
                // \u62d6\u52a8\u6761\u4e0d\u9700\u8981\u6309\u4e0b\u6548\u679c
                return;
            }
            
            console.log(`按钮 ${btn.label} 按下`);
            socket.emit('button_down', { id: btn.id, label: btn.label });
            activeButtonsMap[btnId] = true;
            markDirty();
            // Visual feedback only - key action will be executed on pointer release
        };
        
        // Handle button release (visual only)
        const handleButtonRelease = (btnId) => {
            if (!activeButtonsMap[btnId]) return;
            
            delete activeButtonsMap[btnId];
            markDirty();
            // Visual state cleanup only - no key events emitted
        };
        
        // Execute button action (on final release)
        const executeButtonAction = (btnId) => {
            const btn = buttonsData.value.find(b => b.id === btnId);
            if (!btn) return;
            
            if (btn.type === 'slider') {
                // 拖动条释放后如果设置了自动归中，则重置值
                if (btn.autoCenter) {
                    const rangeMode = btn.rangeMode || 'bipolar';
                    const defaultValue = getSliderDefaultValue(rangeMode);
                    btn.currentValue = defaultValue;
                    socket.emit('slider_value', { id: btn.id, value: defaultValue });
                    markDirty();
                }
                return;
            }
            
            console.log(`按钮 ${btn.label} 抬起`);
            socket.emit('button_up', { id: btn.id });
        };
        
        // 处理拖动条值更新
        const handleSliderMove = (slider, canvasX, canvasY) => {
            const knobSize = slider.orientation === 'horizontal' ? slider.height * 0.8 : slider.width * 0.8;
            const rangeMode = slider.rangeMode || 'bipolar';  // 'bipolar' ([-1, 1]) 或 'unipolar' ([0, 1])
            let value;
            
            if (slider.orientation === 'horizontal') {
                const rangeX = slider.width - knobSize;
                const relativeX = canvasX - slider.x - knobSize / 2;
                const normalizedPos = relativeX / rangeX;
                
                if (rangeMode === 'unipolar') {
                    // unipolar: 从左到右为 0 到 1
                    value = normalizedPos;
                } else {
                    // bipolar: 从左到右为 -1 到 1
                    value = normalizedPos * 2.0 - 1.0;
                }
            } else {
                const rangeY = slider.height - knobSize;
                const relativeY = canvasY - slider.y - knobSize / 2;
                const normalizedPos = relativeY / rangeY;
                
                if (rangeMode === 'unipolar') {
                    // unipolar: 从下到上为 0 到 1
                    value = 1.0 - normalizedPos;
                } else {
                    // bipolar: 从下到上为 -1 到 1
                    value = 1.0 - normalizedPos * 2.0;
                }
            }
            
            // 根据范围模式限制值
            if (rangeMode === 'unipolar') {
                value = Math.max(0.0, Math.min(1.0, value));
            } else {
                value = Math.max(-1.0, Math.min(1.0, value));
            }
            
            slider.currentValue = value;
            
            // 发送到后端
            socket.emit('slider_value', { id: slider.id, value: value });
            markDirty();
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
            
            // 初始化pointer跟踪：记录是否碰到了操控组件
            pointerTouchedControl.set(e.pointerId, hit !== null);
            
            if (isEditing.value) {
                if (!hit) return;
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
                // Normal mode - track pointer even if not on button initially
                // This allows for slide-in detection in pointermove
                if (hit) {
                    pointerToButton.set(e.pointerId, hit.button.id);
                    
                    // \u5982\u679c\u662f\u62d6\u52a8\u6761\uff0c\u7acb\u5373\u5904\u7406\u503c\u66f4\u65b0
                    if (hit.button.type === 'slider') {
                        handleSliderMove(hit.button, x, y);
                    } else {
                        handleButtonPress(hit.button.id);
                    }
                } else {
                    // Track pointer with no button initially
                    pointerToButton.set(e.pointerId, null);
                }
            }
        };
        
        const onCanvasPointerMove = (e) => {
            e.preventDefault();
            const { x, y } = pageToCanvas(e.clientX, e.clientY);
            
            // 如果在这个pointer序列中还没有碰到操控组件，检查当前是否碰到了
            if (!pointerTouchedControl.get(e.pointerId)) {
                const hit = getButtonAtPoint(x, y);
                if (hit) {
                    pointerTouchedControl.set(e.pointerId, true);
                }
            }
            
            if (isEditing.value && dragState) {
                const btn = buttonsData.value[dragState.buttonIndex];
                
                if (dragState.mode === 'move') {
                    btn.x = Math.max(0, Math.min(x - dragState.offsetX, canvasWidth - btn.width));
                    btn.y = Math.max(0, Math.min(y - dragState.offsetY, canvasHeight - btn.height));
                } else if (dragState.mode === 'resize') {
                    const deltaX = x - dragState.startX;
                    const deltaY = y - dragState.startY;
                    btn.width = Math.max(MIN_BUTTON_SIZE, Math.min(MAX_BUTTON_SIZE, dragState.startWidth + deltaX));
                    btn.height = Math.max(MIN_BUTTON_SIZE, Math.min(MAX_BUTTON_SIZE, dragState.startHeight + deltaY));
                }
                markDirty();
            } else if (!isEditing.value) {
                // Check if pointer moved to different button
                // Only handle tracked pointers
                if (!pointerToButton.has(e.pointerId)) return;
                
                const currentBtnId = pointerToButton.get(e.pointerId);
                const hit = getButtonAtPoint(x, y);
                const newBtnId = hit ? hit.button.id : null;
                
                // \u5982\u679c\u5f53\u524d\u6309\u94ae\u662f\u62d6\u52a8\u6761\uff0c\u5904\u7406\u62d6\u52a8
                if (currentBtnId && hit && hit.button.id === currentBtnId && hit.button.type === 'slider') {
                    handleSliderMove(hit.button, x, y);
                } else if (newBtnId !== currentBtnId) {
                    // Release old button
                    if (currentBtnId) {
                        handleButtonRelease(currentBtnId);
                    }
                    // Press new button or update to null
                    pointerToButton.set(e.pointerId, newBtnId);
                    if (newBtnId) {
                        const newBtn = buttonsData.value.find(b => b.id === newBtnId);
                        if (newBtn && newBtn.type === 'slider') {
                            handleSliderMove(newBtn, x, y);
                        } else {
                            handleButtonPress(newBtnId);
                        }
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
                    // Execute the button action on release
                    executeButtonAction(btnId);
                    // Clear visual state
                    handleButtonRelease(btnId);
                    pointerToButton.delete(e.pointerId);
                }
                
                // 检查整个pointer序列是否没有碰到操控组件
                const touchedControl = pointerTouchedControl.get(e.pointerId);
                if (!touchedControl) {
                    // 如果没有碰到操控组件，发送隐藏overlay的命令
                    socket.emit('hide_overlay');
                }
                
                // 清理跟踪状态
                pointerTouchedControl.delete(e.pointerId);
            }
        };
        
        // 双击以编辑按钮
        const onCanvasDoubleClick = (e) => {
            if (!isEditing.value) return;
            
            const { x, y } = pageToCanvas(e.clientX, e.clientY);
            const hit = getButtonAtPoint(x, y);
            
            if (hit) {
                editButton(hit.button);
            }
        };
        
        // 编辑模式相关函数
        const toggleEditMode = () => {
            isEditing.value = !isEditing.value;
            // 进入编辑模式时清除激活按键
            if (isEditing.value) {
                Object.keys(activeButtonsMap).forEach(btnId => {
                    handleButtonRelease(btnId);
                });
                pointerToButton.clear();
            }
            markDirty();
        };
        
        const saveLayout = () => {
            socket.emit('save_layout', buttonsData.value);
        };
        
        const editButton = (btn) => {
            if (!isEditing.value) return;
            
            Object.assign(editingButton, {
                id: btn.id,
                type: btn.type || 'button',
                label: btn.label,
                keys: [...(btn.keys || [])],
                colorIndex: btn.colorIndex !== undefined ? btn.colorIndex : 0,
                width: btn.width || 100,
                height: btn.height || 100,
                x: btn.x,
                y: btn.y,
                orientation: btn.orientation || 'horizontal',
                autoCenter: btn.autoCenter !== undefined ? btn.autoCenter : true,
                rangeMode: btn.rangeMode || 'bipolar'  // 向后兼容：旧的拖动条默认为bipolar
            });
            showEditDialog.value = true;
        };
        
        const addNewButton = () => {
            Object.assign(editingButton, {
                id: '',
                type: 'button',
                label: 'New',
                keys: [],
                colorIndex: 0,
                width: 80,
                height: 80,
                x: 50,
                y: 50,
                orientation: 'horizontal',
                autoCenter: true,
                axis: 'right_x'
            });
            showEditDialog.value = true;
        };
        
        const addNewSlider = () => {
            Object.assign(editingButton, {
                id: '',
                type: 'slider',
                label: 'Slider',
                keys: [],
                colorIndex: 0,
                width: 200,  // 横向拖动条默认宽度
                height: 60,  // 横向拖动条默认高度
                x: 50,
                y: 50,
                orientation: 'horizontal',
                autoCenter: true,
                axis: 'right_x',
                rangeMode: 'unipolar',  // 新拖动条默认为 unipolar 模式（居中=0.5）
                currentValue: getSliderDefaultValue('unipolar')
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
                type: editingButton.type,
                label: editingButton.label,
                keys: editingButton.keys,
                colorIndex: editingButton.colorIndex,
                width: editingButton.width,
                height: editingButton.height,
                x: editingButton.x,
                y: editingButton.y
            };
            
            // 如果是拖动条，添加拖动条特有属性
            if (editingButton.type === 'slider') {
                buttonData.orientation = editingButton.orientation;
                buttonData.autoCenter = editingButton.autoCenter;
                buttonData.rangeMode = editingButton.rangeMode || 'bipolar';
                buttonData.currentValue = editingButton.currentValue !== undefined ? editingButton.currentValue : getSliderDefaultValue(buttonData.rangeMode);
                // 不再保存 axis 属性，因为轴绑定现在在驾驶配置中统一管理
            }
            
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
                    // 添加新按钮
                    const response = await fetch('/api/add_button', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(buttonData)
                    });
                    const result = await response.json();
                    buttonData.id = result.id;
                    buttonsData.value.push(buttonData);
                }
                
                markDirty();
                showEditDialog.value = false;
            } catch (error) {
                console.error('保存按钮失败：', error);
                showMessage.error('保存按钮失败');
            }
        };
        
        const saveDrivingConfig = async () => {
            try {
                console.log('开始保存驾驶配置...');
                console.log('当前drivingConfig:', drivingConfig);
                console.log('摇杆类型:', joystickType.value);
                
                // 准备要保存的配置数据
                const configToSave = {
                    joystick_type: joystickType.value
                };
                
                if (joystickType.value === 'custom') {
                    // 自定义摇杆模式：保存自定义轴映射
                    configToSave.custom_joystick = {
                        axis_count: customJoystickAxisCount.value,
                        axis_mapping: {}
                    };
                    
                    // 转换 customAxisMapping 为普通对象（因为可能是 reactive）
                    for (let i = 0; i < customJoystickAxisCount.value; i++) {
                        if (customAxisMapping[i]) {
                            configToSave.custom_joystick.axis_mapping[i] = {
                                source_type: customAxisMapping[i].source_type,
                                source_id: customAxisMapping[i].source_id,
                                peak_value: customAxisMapping[i].peak_value,
                                deadzone: customAxisMapping[i].deadzone,
                                gyro_range: customAxisMapping[i].gyro_range,
                                invert: customAxisMapping[i].invert || false
                            };
                        }
                    }
                } else {
                    // Xbox 360 模式：保存原有的轴配置
                    // 更新旧的 gyro_axis_mapping 和 sliders（保持向后兼容）
                    const newGyroMapping = { gamma: null, beta: null, alpha: null };
                    const newSliders = [];
                    
                    // 从统一轴配置中反向生成旧格式
                    Object.entries(drivingConfig.axis_config).forEach(([axis, config]) => {
                        if (config.source_type === 'gyro' && config.source_id) {
                            newGyroMapping[config.source_id] = axis;
                        } else if (config.source_type === 'slider' && config.source_id) {
                            const sliderBtn = buttonsData.value.find(b => b.id === config.source_id && b.type === 'slider');
                            if (sliderBtn) {
                                newSliders.push({
                                    id: sliderBtn.id,
                                    label: sliderBtn.label,
                                    axis: axis,
                                    orientation: sliderBtn.orientation,
                                    autoCenter: sliderBtn.autoCenter
                                });
                            }
                        }
                    });
                    
                    drivingConfig.gyro_axis_mapping = newGyroMapping;
                    drivingConfig.sliders = newSliders;
                    
                    configToSave.driving_config = drivingConfig;
                }
                
                console.log('准备发送请求，数据:', configToSave);
                const response = await fetch('/api/update_driving_config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(configToSave)
                });
                
                console.log('收到响应:', response.status, response.statusText);
                
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const result = await response.json();
                console.log('保存驾驶配置响应:', result);
                
                showMessage.success('驾驶配置已保存，请重启服务器以应用更改');
            } catch (error) {
                console.error('保存驾驶配置失败：', error);
                showMessage.error('保存驾驶配置失败: ' + error.message);
            }
        };
        
        const openDrivingConfig = () => {
            showDrivingConfigDialog.value = true;
        };
        
        // 拖动条方向变化时自动调整大小
        const onSliderOrientationChange = (newOrientation) => {
            if (newOrientation === 'horizontal') {
                // 横向：宽 > 高
                if (editingButton.width < editingButton.height) {
                    const temp = editingButton.width;
                    editingButton.width = editingButton.height;
                    editingButton.height = temp;
                }
                // 确保至少是推荐尺寸
                if (editingButton.width < 150) editingButton.width = 200;
                if (editingButton.height > 80) editingButton.height = 60;
            } else {
                // 竖向：高 > 宽
                if (editingButton.height < editingButton.width) {
                    const temp = editingButton.width;
                    editingButton.width = editingButton.height;
                    editingButton.height = temp;
                }
                // 确保至少是推荐尺寸
                if (editingButton.height < 150) editingButton.height = 200;
                if (editingButton.width > 80) editingButton.width = 60;
            }
            markDirty();
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
                markDirty();
                showEditDialog.value = false;
            } catch (error) {
                console.error('Failed to delete button:', error);
                showMessage.error('Failed to delete button');
            }
        };
        
        // 驾驶模式相关函数
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
                
                // 设置双击处理
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
            // Clear any pending button timeouts
            pendingButtonTimeouts.forEach(timeoutId => clearTimeout(timeoutId));
            pendingButtonTimeouts.clear();
            window.removeEventListener('resize', resizeCanvas);
        });
        
        return {
            canvasRef,
            buttonsData,
            slidersData,
            isEditing,
            mode,
            modifierKeys,
            specialKeys,
            showEditDialog,
            showDrivingConfigDialog,
            editingButton,
            selectedModifiers,
            selectedSpecialKey,
            customKeyInput,
            showMainDeviceDialog,
            hasExistingMainDevice,
            isMainDevice,
            gyroData,
            drivingConfig,
            dialogWidth,
            activeButtonsMap,
            BUTTON_COLORS,
            axisConfigList,
            customAxisConfigList,
            joystickType,
            customJoystickAxisCount,
            getAxisDisplayName,
            getAvailableSlidersForAxis,
            getAvailableSlidersForCustomAxis,
            onAxisSourceTypeChange,
            onCustomAxisSourceTypeChange,
            onJoystickTypeChange,
            onCustomAxisCountChange,
            toggleEditMode,
            saveLayout,
            editButton,
            addNewButton,
            addNewSlider,
            addKey,
            removeKey,
            saveButtonEdit,
            saveDrivingConfig,
            openDrivingConfig,
            onSliderOrientationChange,
            deleteButton,
            setAsMainDevice
        };
    }
});

app.use(ElementPlus);
app.mount('#app');
