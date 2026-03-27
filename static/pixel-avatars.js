// =============================================
// PIXEL AVATARS - 8-Bit Character System
// Loaded dynamically when pixel avatars are enabled
// =============================================

(function () {
    'use strict';

    // === BASE PALETTE (0-f hex) ===
    const BASE_PALETTE = {
        '0': null,             // transparent
        '1': '#111111',        // black / outlines
        '2': '#5c3018',        // dark brown (hats, hair)
        '3': '#8b5a2b',        // medium brown (leather, wood)
        '4': '#d4a574',        // skin tone 1 (light)
        '5': '#f5deb3',        // skin highlight
        '6': '#ffffff',        // white
        '7': '#cc2222',        // red
        '8': '#ffd700',        // gold / yellow
        '9': '#1a1a80',        // navy blue
        'a': '#888888',        // grey / silver
        'b': '#336633',        // green
        'c': '#a0784a',        // skin tone 2 (medium)
        'd': '#6b4226',        // skin tone 3 (dark)
        'e': '#7b3f8e',        // purple
        'f': '#4488cc',        // light blue
    };

    // === SKIN TONE SWAPS ===
    const SKIN = {
        light:  { '4': '#d4a574', '5': '#f5deb3' },
        medium: { '4': '#a07848', '5': '#c89860' },
        dark:   { '4': '#6b4226', '5': '#8b6240' },
    };

    // === HAIR COLOR SWAPS ===
    const HAIR = {
        brown:  { '2': '#5c3018' },
        black:  { '2': '#222222' },
        red:    { '2': '#8b2500' },
        blonde: { '2': '#c8a050' },
        grey:   { '2': '#777777' },
    };

    // ===================================================
    // BASE SPRITES - 16x16 pixel art (each row = 16 hex chars)
    // Palette key: 4/5=skin, 2=hair/hat-dark, 3=hat-med/leather,
    //   7=red, 8=gold, 9=navy, 6=white, 1=black, a=grey, b=green
    // ===================================================

    const SPRITES = {

        // --- CAPTAIN (Male) - Tricorn hat, red coat, gold epaulettes ---
        captain_m: [
            '0000000000000000',
            '0000012221000000',
            '0000122222100000',
            '0011222222211000',
            '0000014441000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000188881000000',
            '0000177871000000',
            '0001777877100000',
            '0000177871000000',
            '0000018810000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- CAPTAIN (Female) - Tricorn with flowing hair ---
        captain_f: [
            '0000000000000000',
            '0000012221000000',
            '0000122222100000',
            '0011222222211000',
            '0002144441200000',
            '0002414114200000',
            '0000044540000000',
            '0000214412000000',
            '0000188881000000',
            '0000177871000000',
            '0001777877100000',
            '0000177871000000',
            '0000018810000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- FIRST MATE (Male) - Red bandana, open leather vest ---
        firstmate_m: [
            '0000000000000000',
            '0000000000000000',
            '0000077770000000',
            '0000777777000000',
            '0000744447000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000033330000000',
            '0000364463000000',
            '0000366663000000',
            '0000133331000000',
            '0000013310000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- FIRST MATE (Female) - Bandana, longer hair ---
        firstmate_f: [
            '0000000000000000',
            '0000000000000000',
            '0000077770000000',
            '0000777777000000',
            '0002744447200000',
            '0002414114200000',
            '0000044540000000',
            '0000214412000000',
            '0000033330000000',
            '0000364463000000',
            '0000366663000000',
            '0000133331000000',
            '0000013310000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- DECKHAND - Messy hair, striped shirt ---
        deckhand: [
            '0000000000000000',
            '0000000000000000',
            '0000022020000000',
            '0000022220000000',
            '0000244442000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000067670000000',
            '0000676767000000',
            '0000067670000000',
            '0000167671000000',
            '0000013310000000',
            '0000099990000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- GUNNER - Cap, eyepatch, bandolier ---
        gunner: [
            '0000000000000000',
            '0000000000000000',
            '0000011110000000',
            '0000111111000000',
            '0000144441000000',
            '0000114114000000',
            '0000044540000000',
            '0000014410000000',
            '0000033330000000',
            '0000383833000000',
            '0000338383000000',
            '0000133331000000',
            '0000018810000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- NAVIGATOR - Wide-brim hat, spyglass ---
        navigator: [
            '0000000000000000',
            '0000033330000000',
            '0000333333000000',
            '0013333333310000',
            '0000144441000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000099990000000',
            '0000999999000000',
            '0000999989000000',
            '0000199991000000',
            '0000018810000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- QUARTERMASTER - Simple hat, keys on belt ---
        quartermaster: [
            '0000000000000000',
            '0000000000000000',
            '0000022220000000',
            '0000222222000000',
            '0000144441000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000033330000000',
            '0000333333000000',
            '0008333333000000',
            '0000133331000000',
            '0000083380000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- LOOKOUT - Tall top hat, vest ---
        lookout: [
            '0000011110000000',
            '0000011110000000',
            '0000011110000000',
            '0000111111000000',
            '0000144441000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000066660000000',
            '0000366663000000',
            '0000366663000000',
            '0000133331000000',
            '0000013310000000',
            '0000011110000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- EAST INDIA CO. OFFICER - Powdered wig, blue uniform ---
        eic_officer: [
            '0000000000000000',
            '0000066660000000',
            '0000666666000000',
            '0000666666000000',
            '0000644446000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000088880000000',
            '0000999899000000',
            '0000999899000000',
            '0000199991000000',
            '0000088880000000',
            '0000066660000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- BRITISH REDCOAT - Shako hat, red uniform, white crossbelt ---
        redcoat: [
            '0000000000000000',
            '0000011110000000',
            '0000011110000000',
            '0000811118000000',
            '0000144441000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000068860000000',
            '0000777877000000',
            '0000777877000000',
            '0000177771000000',
            '0000088880000000',
            '0000066660000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- NAVAL OFFICER - Bicorn hat, navy coat ---
        naval_officer: [
            '0000000000000000',
            '0000099990000000',
            '0000999999000000',
            '0019999999910000',
            '0000844448000000',
            '0000414114000000',
            '0000044540000000',
            '0000014410000000',
            '0000088880000000',
            '0000999899000000',
            '0000999899000000',
            '0000199991000000',
            '0000088880000000',
            '0000099990000000',
            '0000011011000000',
            '0000000000000000',
        ],

        // --- SKELETON - Bones, hollow eyes ---
        skeleton: [
            '0000000000000000',
            '0000000000000000',
            '0000016610000000',
            '0000166661000000',
            '0000616116000000',
            '0000166661000000',
            '0000061160000000',
            '0000006600000000',
            '0000016610000000',
            '0000166661000000',
            '0000060060000000',
            '0000166661000000',
            '0000006600000000',
            '0000066660000000',
            '0000060060000000',
            '0000000000000000',
        ],

        // --- PARROT - Colorful tropical bird ---
        parrot: [
            '0000000000000000',
            '0000000000000000',
            '0000088800000000',
            '0000888880000000',
            '0000818880000000',
            '0000028800000000',
            '0000088800000000',
            '000b877b00000000',
            '000bb77bb0000000',
            '00bbb77bbb000000',
            '000bb77bb0000000',
            '0000077000000000',
            '0000fff000000000',
            '0000fff000000000',
            '0000080800000000',
            '0000030300000000',
        ],

        // --- OCTOPUS / KRAKEN - Tentacles ---
        octopus: [
            '0000000000000000',
            '0000000000000000',
            '0000019910000000',
            '0000199991000000',
            '0000961169000000',
            '0000999999000000',
            '0009999999900000',
            '0009999999900000',
            '0099009900990000',
            '0900900090090000',
            '9009000009090000',
            '9000900090009000',
            '0009000009000000',
            '0000000000000000',
            '0000000000000000',
            '0000000000000000',
        ],

        // --- MERMAID - Fish tail ---
        mermaid: [
            '0000000000000000',
            '0000022220000000',
            '0000222222000000',
            '0002244422200000',
            '0000414114000000',
            '0000044540000000',
            '0000214412000000',
            '0000044440000000',
            '0000044440000000',
            '000004ee40000000',
            '0000eeeeee000000',
            '000eee11eee00000',
            '00ee0011000e0000',
            '0e00001100000000',
            '0000011110000000',
            '0000110011000000',
        ],

        // --- SHARK - Menacing sea creature ---
        shark: [
            '0000000000000000',
            '0000000000000000',
            '0000000000000000',
            '0000001000000000',
            '0000011a00000000',
            '0000111aa0000000',
            '000a11aaaa000000',
            '00aaa1aaaaaaa000',
            '0aaaa1aaaaaa0000',
            '0aaaa1aaaa6a0000',
            '00aaaaaaaaa00000',
            '000a6a6a6a000000',
            '0000aaaa00000000',
            '000000000a000000',
            '0000000000a00000',
            '0000000000000000',
        ],
    };

    // ===================================================
    // CHARACTER DEFINITIONS
    // Each character = base sprite + palette overrides
    // ===================================================

    const CHARACTERS = [
        // --- PIRATES ---
        // Captains (6 variants)
        { id: 'captain_m_light', base: 'captain_m', name: 'Captain', category: 'Pirates', skin: 'light', hair: 'brown' },
        { id: 'captain_m_med', base: 'captain_m', name: 'Captain', category: 'Pirates', skin: 'medium', hair: 'black' },
        { id: 'captain_m_dark', base: 'captain_m', name: 'Captain', category: 'Pirates', skin: 'dark', hair: 'black' },
        { id: 'captain_f_light', base: 'captain_f', name: 'Captain', category: 'Pirates', skin: 'light', hair: 'red' },
        { id: 'captain_f_med', base: 'captain_f', name: 'Captain', category: 'Pirates', skin: 'medium', hair: 'brown' },
        { id: 'captain_f_dark', base: 'captain_f', name: 'Captain', category: 'Pirates', skin: 'dark', hair: 'black' },

        // First Mates (4 variants)
        { id: 'firstmate_m_light', base: 'firstmate_m', name: 'First Mate', category: 'Pirates', skin: 'light', hair: 'brown' },
        { id: 'firstmate_m_dark', base: 'firstmate_m', name: 'First Mate', category: 'Pirates', skin: 'dark', hair: 'black' },
        { id: 'firstmate_f_light', base: 'firstmate_f', name: 'First Mate', category: 'Pirates', skin: 'light', hair: 'blonde' },
        { id: 'firstmate_f_dark', base: 'firstmate_f', name: 'First Mate', category: 'Pirates', skin: 'medium', hair: 'black' },

        // Deckhands (3 variants)
        { id: 'deckhand_light', base: 'deckhand', name: 'Deckhand', category: 'Pirates', skin: 'light', hair: 'blonde' },
        { id: 'deckhand_med', base: 'deckhand', name: 'Deckhand', category: 'Pirates', skin: 'medium', hair: 'brown' },
        { id: 'deckhand_dark', base: 'deckhand', name: 'Deckhand', category: 'Pirates', skin: 'dark', hair: 'black' },

        // Gunners (2 variants)
        { id: 'gunner_light', base: 'gunner', name: 'Gunner', category: 'Pirates', skin: 'light', hair: 'brown' },
        { id: 'gunner_dark', base: 'gunner', name: 'Gunner', category: 'Pirates', skin: 'dark', hair: 'black' },

        // Navigator (2 variants)
        { id: 'navigator_light', base: 'navigator', name: 'Navigator', category: 'Pirates', skin: 'light', hair: 'grey' },
        { id: 'navigator_dark', base: 'navigator', name: 'Navigator', category: 'Pirates', skin: 'medium', hair: 'brown' },

        // Quartermaster (2 variants)
        { id: 'quartermaster_light', base: 'quartermaster', name: 'Quartermaster', category: 'Pirates', skin: 'light', hair: 'brown' },
        { id: 'quartermaster_dark', base: 'quartermaster', name: 'Quartermaster', category: 'Pirates', skin: 'dark', hair: 'grey' },

        // Lookout (2 variants)
        { id: 'lookout_light', base: 'lookout', name: 'Lookout', category: 'Pirates', skin: 'light', hair: 'brown' },
        { id: 'lookout_dark', base: 'lookout', name: 'Lookout', category: 'Pirates', skin: 'medium', hair: 'black' },

        // --- MILITARY ---
        { id: 'eic_officer_light', base: 'eic_officer', name: 'EIC Officer', category: 'Military', skin: 'light', hair: 'brown' },
        { id: 'eic_officer_dark', base: 'eic_officer', name: 'EIC Officer', category: 'Military', skin: 'medium', hair: 'brown' },
        { id: 'redcoat_light', base: 'redcoat', name: 'Redcoat', category: 'Military', skin: 'light', hair: 'brown' },
        { id: 'redcoat_dark', base: 'redcoat', name: 'Redcoat', category: 'Military', skin: 'dark', hair: 'black' },
        { id: 'naval_light', base: 'naval_officer', name: 'Naval Officer', category: 'Military', skin: 'light', hair: 'brown' },
        { id: 'naval_dark', base: 'naval_officer', name: 'Naval Officer', category: 'Military', skin: 'dark', hair: 'black' },

        // --- FANTASY ---
        { id: 'skeleton', base: 'skeleton', name: 'Skeleton', category: 'Fantasy', skin: null, hair: null },
        { id: 'parrot', base: 'parrot', name: 'Parrot', category: 'Fantasy', skin: null, hair: null },
        { id: 'octopus', base: 'octopus', name: 'Kraken', category: 'Fantasy', skin: null, hair: null },
        { id: 'mermaid', base: 'mermaid', name: 'Mermaid', category: 'Fantasy', skin: 'light', hair: 'blonde' },
        { id: 'mermaid_dark', base: 'mermaid', name: 'Mermaid', category: 'Fantasy', skin: 'dark', hair: 'black' },
        { id: 'shark', base: 'shark', name: 'Shark', category: 'Fantasy', skin: null, hair: null },
    ];

    // === AI CHARACTER MAPPING (fixed assignments) ===
    const AI_CHARACTERS = {
        'Davy Jones': 'octopus',
        'Blackbeard': 'captain_m_dark',
        'Red Beard': 'firstmate_m_light',
        'Salty Pete': 'deckhand_med',
        'One-Eyed Willy': 'skeleton',
    };

    // ===================================================
    // RENDERING ENGINE (Canvas-based)
    // ===================================================

    const spriteCache = {};

    function buildPalette(character) {
        const pal = Object.assign({}, BASE_PALETTE);
        if (character.skin && SKIN[character.skin]) {
            Object.assign(pal, SKIN[character.skin]);
        }
        if (character.hair && HAIR[character.hair]) {
            Object.assign(pal, HAIR[character.hair]);
        }
        return pal;
    }

    function renderToDataURL(spriteRows, palette, scale) {
        scale = scale || 4;
        const size = 16;
        const canvas = document.createElement('canvas');
        canvas.width = size * scale;
        canvas.height = size * scale;
        const ctx = canvas.getContext('2d');

        // Disable smoothing for crisp pixels
        ctx.imageSmoothingEnabled = false;

        for (let y = 0; y < size; y++) {
            const row = spriteRows[y];
            if (!row) continue;
            for (let x = 0; x < size; x++) {
                const ch = row[x];
                if (!ch || ch === '0') continue;
                const color = palette[ch];
                if (!color) continue;
                ctx.fillStyle = color;
                ctx.fillRect(x * scale, y * scale, scale, scale);
            }
        }

        return canvas.toDataURL('image/png');
    }

    function getSpriteDataURL(characterId, scale) {
        scale = scale || 4;
        const cacheKey = characterId + '_' + scale;
        if (spriteCache[cacheKey]) return spriteCache[cacheKey];

        const character = CHARACTERS.find(c => c.id === characterId);
        if (!character) return null;

        const spriteRows = SPRITES[character.base];
        if (!spriteRows) return null;

        const palette = buildPalette(character);
        const dataURL = renderToDataURL(spriteRows, palette, scale);
        spriteCache[cacheKey] = dataURL;
        return dataURL;
    }

    // ===================================================
    // ANIMATION SYSTEM
    // ===================================================

    const activeAnimations = {};

    function triggerAnimation(playerIdx, type, duration) {
        const card = document.querySelector(`[data-player-idx="${playerIdx}"]`);
        if (!card) return;

        // Clear existing non-permanent animation
        const existing = activeAnimations[playerIdx];
        if (existing && existing.type !== 'eliminated' && existing.type !== 'idle') {
            card.classList.remove('px-anim-' + existing.type);
            clearTimeout(existing.timer);
        }

        // Don't override eliminated
        if (activeAnimations[playerIdx]?.type === 'eliminated' && type !== 'eliminated') {
            return;
        }

        const animClass = 'px-anim-' + type;
        card.classList.add(animClass);

        const durations = {
            idle: 0,       // infinite
            roll: 600,
            bid: 800,
            liar: 1000,
            win: 1000,
            lose: 800,
            chat: 700,
            think: 0,     // infinite until next action
            eliminated: 0, // permanent
        };

        const dur = duration || durations[type] || 800;

        if (dur > 0) {
            const timer = setTimeout(() => {
                card.classList.remove(animClass);
                // Restore idle
                if (!card.classList.contains('px-anim-eliminated')) {
                    card.classList.add('px-anim-idle');
                }
                delete activeAnimations[playerIdx];
            }, dur);

            activeAnimations[playerIdx] = { type, timer };
        } else {
            activeAnimations[playerIdx] = { type, timer: null };
        }
    }

    function triggerMyAnimation(type, duration) {
        const myWrap = document.querySelector('.px-my-avatar');
        if (!myWrap) return;

        const existing = myWrap.dataset.pxAnim;
        if (existing && existing !== 'idle') {
            myWrap.classList.remove('px-anim-' + existing);
        }

        const animClass = 'px-anim-' + type;
        myWrap.classList.add(animClass);
        myWrap.dataset.pxAnim = type;

        const durations = {
            idle: 0, roll: 600, bid: 800, liar: 1000,
            win: 1000, lose: 800, chat: 700, eliminated: 0,
        };
        const dur = duration || durations[type] || 800;

        if (dur > 0) {
            setTimeout(() => {
                myWrap.classList.remove(animClass);
                myWrap.classList.add('px-anim-idle');
                myWrap.dataset.pxAnim = 'idle';
            }, dur);
        }
    }

    // ===================================================
    // OPPONENT CARD RENDERING
    // ===================================================

    function getAvatarHTML(characterId, extraClass) {
        const url = getSpriteDataURL(characterId, 4);
        if (!url) return '';
        return `<div class="px-sprite-wrap ${extraClass || ''}"><img src="${url}" alt="pixel avatar"></div>`;
    }

    function getSmallAvatarHTML(characterId) {
        const url = getSpriteDataURL(characterId, 3);
        if (!url) return '';
        return `<img src="${url}" alt="" style="width:40px;height:40px;image-rendering:pixelated;">`;
    }

    // ===================================================
    // CHARACTER ASSIGNMENT
    // ===================================================

    // Simple name hash for consistent character assignment
    function nameHash(name) {
        let hash = 0;
        for (let i = 0; i < name.length; i++) {
            hash = ((hash << 5) - hash) + name.charCodeAt(i);
            hash |= 0;
        }
        return Math.abs(hash);
    }

    // Resolve which pixel character a player should show
    function resolveCharacter(player, idx) {
        // AI players: fixed mapping
        if (!player.is_human && AI_CHARACTERS[player.name]) {
            return AI_CHARACTERS[player.name];
        }

        // AI fallback: assign based on index
        if (!player.is_human) {
            const fallbacks = ['captain_m_dark', 'firstmate_m_light', 'deckhand_dark', 'gunner_light', 'lookout_dark'];
            return fallbacks[idx % fallbacks.length];
        }

        // Local player: use their selected pixel avatar
        if (typeof playerIndex !== 'undefined' && idx === playerIndex) {
            const selected = localStorage.getItem('pixelAvatar');
            if (selected && CHARACTERS.find(c => c.id === selected)) {
                return selected;
            }
        }

        // Other human players: consistent assignment based on name hash
        if (player.is_human && typeof playerIndex !== 'undefined' && idx !== playerIndex) {
            const humanChars = CHARACTERS.filter(c => c.category === 'Pirates');
            return humanChars[nameHash(player.name) % humanChars.length].id;
        }

        // Default
        return 'captain_m_light';
    }

    // ===================================================
    // CHARACTER PICKER UI
    // ===================================================

    function buildCharacterPicker(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const categories = {};
        CHARACTERS.forEach(ch => {
            if (!categories[ch.category]) categories[ch.category] = [];
            categories[ch.category].push(ch);
        });

        const selected = localStorage.getItem('pixelAvatar') || 'captain_m_light';

        let html = '<div class="px-char-grid">';
        for (const [cat, chars] of Object.entries(categories)) {
            html += `<div class="px-cat-header">⚓ ${cat}</div>`;
            chars.forEach(ch => {
                const url = getSpriteDataURL(ch.id, 3);
                const sel = ch.id === selected ? ' selected' : '';
                html += `<div class="px-char-option${sel}" data-char-id="${ch.id}" onclick="PixelAvatars.selectCharacter('${ch.id}', '${containerId}')">
                    <img src="${url}" alt="${ch.name}">
                    <div class="px-char-label">${ch.name}</div>
                </div>`;
            });
        }
        html += '</div>';

        container.innerHTML = html;
    }

    function selectCharacter(charId, containerId) {
        localStorage.setItem('pixelAvatar', charId);

        // Update selection UI
        const container = document.getElementById(containerId);
        if (container) {
            container.querySelectorAll('.px-char-option').forEach(el => {
                el.classList.toggle('selected', el.dataset.charId === charId);
            });
        }

        // Update any visible pixel avatars
        if (typeof updateUI === 'function') {
            updateUI();
        }
    }

    // ===================================================
    // PRELOAD - render all sprites to cache on init
    // ===================================================

    function preloadAll() {
        CHARACTERS.forEach(ch => {
            getSpriteDataURL(ch.id, 4); // game size
            getSpriteDataURL(ch.id, 3); // picker size
        });
    }

    // ===================================================
    // PUBLIC API
    // ===================================================

    window.PixelAvatars = {
        characters: CHARACTERS,
        aiCharacters: AI_CHARACTERS,
        getSpriteDataURL: getSpriteDataURL,
        getAvatarHTML: getAvatarHTML,
        getSmallAvatarHTML: getSmallAvatarHTML,
        triggerAnimation: triggerAnimation,
        triggerMyAnimation: triggerMyAnimation,
        resolveCharacter: resolveCharacter,
        buildCharacterPicker: buildCharacterPicker,
        selectCharacter: selectCharacter,
        preloadAll: preloadAll,
    };

    // Preload on next idle frame
    if (window.requestIdleCallback) {
        requestIdleCallback(preloadAll);
    } else {
        setTimeout(preloadAll, 100);
    }

})();
