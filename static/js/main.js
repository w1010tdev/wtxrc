const socket = io();
const gamePad = document.getElementById('game-pad');
let buttonsData = [];
let isEditing = false;
let draggedButton = null;
let offset = { x: 0, y: 0 };

// Initial Load
fetch('/api/config')
    .then(response => response.json())
    .then(data => {
        buttonsData = data.buttons;
        renderButtons();
    });

function renderButtons() {
    gamePad.innerHTML = '';
    buttonsData.forEach((btn, index) => {
        const el = document.createElement('div');
        el.className = 'game-btn';
        el.innerText = btn.label;
        el.style.backgroundColor = btn.color || '#555';
        el.style.left = btn.x + 'px';
        el.style.top = btn.y + 'px';
        el.style.width = btn.width + 'px';
        el.style.height = btn.height + 'px';
        el.dataset.id = btn.id;
        el.dataset.index = index;

        // Interaction Events
        addInteractionEvents(el, btn);

        gamePad.appendChild(el);
    });
}

function addInteractionEvents(el, btnData) {
    // Touch Events for Control
    el.addEventListener('touchstart', (e) => {
        if (isEditing) handleDragStart(e, el);
        else handlePress(e, btnData);
    }, { passive: false });

    el.addEventListener('touchend', (e) => {
        if (isEditing) handleDragEnd(e, el);
        else handleRelease(e, btnData);
    }, { passive: false });
    
    // Mouse Events for PC testing
    el.addEventListener('mousedown', (e) => {
        if (isEditing) handleDragStart(e, el);
        else handlePress(e, btnData);
    });
    
    document.addEventListener('mouseup', (e) => {
       // specific logic handled in drag
    });

    el.addEventListener('mouseup', (e) => {
        if (!isEditing) handleRelease(e, btnData);
    });
}

// Control Logic
function handlePress(e, btn) {
    e.preventDefault();
    socket.emit('button_down', { id: btn.id, label: btn.label });
    e.target.style.opacity = '0.7';
}

function handleRelease(e, btn) {
    e.preventDefault();
    socket.emit('button_up', { id: btn.id });
    e.target.style.opacity = '1';
}

// Edit Mode Logic
function toggleEditMode() {
    isEditing = !isEditing;
    const btn = document.getElementById('toggle-edit-btn');
    const saveBtn = document.getElementById('save-btn');
    
    if (isEditing) {
        btn.innerText = 'Exit Edit Mode';
        btn.classList.add('editing');
        saveBtn.style.display = 'inline-block';
        document.querySelectorAll('.game-btn').forEach(b => b.classList.add('editing'));
    } else {
        btn.innerText = 'Enable Edit Mode';
        btn.classList.remove('editing');
        saveBtn.style.display = 'none';
        document.querySelectorAll('.game-btn').forEach(b => b.classList.remove('editing'));
    }
}

function saveLayout() {
    socket.emit('save_layout', buttonsData);
}

socket.on('layout_saved', (data) => {
    alert('Layout Saved!');
    toggleEditMode();
});

// Drag Logic (simplified for touch/mouse)
function handleDragStart(e, el) {
    if (!isEditing) return;
    draggedButton = el;
    
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    
    const rect = el.getBoundingClientRect();
    offset.x = clientX - rect.left;
    offset.y = clientY - rect.top;
    
    // Attach move listener globally to document to catch fast movements
    document.addEventListener('touchmove', onMove, { passive: false });
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onEnd);
    document.addEventListener('touchend', onEnd); // ensure we clean up
}


function onMove(e) {
    if (!draggedButton) return;
    e.preventDefault();
    
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    
    const gamePadRect = gamePad.getBoundingClientRect();
    
    let newX = clientX - gamePadRect.left - offset.x;
    let newY = clientY - gamePadRect.top - offset.y;
    
    // Snap/Boundaries logic could go here
    
    draggedButton.style.left = newX + 'px';
    draggedButton.style.top = newY + 'px';
    
    // Update data model
    const index = draggedButton.dataset.index;
    buttonsData[index].x = newX;
    buttonsData[index].y = newY;
}

function onEnd(e) {
    handleDragEnd(e, draggedButton);
}

function handleDragEnd(e, el) {
    if (!draggedButton) return;
    draggedButton = null;
    document.removeEventListener('touchmove', onMove);
    document.removeEventListener('mousemove', onMove);
    document.removeEventListener('mouseup', onEnd);
    document.removeEventListener('touchend', onEnd);
}
