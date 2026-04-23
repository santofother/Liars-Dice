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

        // ============================================
        // LEGENDARY SKINS — distinct sprites
        // ============================================

        // --- GHOST CAPTAIN - Ethereal white spectre with tricorn ---
        legendary_ghost: [
            '0000000000000000',
            '0000016661000000',
            '0000166666100000',
            '0011666666611000',
            '0000a66666a00000',
            '0000616616a00000',
            '00000a666a000000',
            '0000016661000000',
            '0000066660000000',
            '0000a6666a000000',
            '0006a6666a600000',
            '0000666666000000',
            '00000a66a0000000',
            '0000a000a0000000',
            '00000a000a000000',
            '0000000000000000',
        ],

        // --- BONE PIRATE - Skeleton with red bandana ---
        legendary_skeleton: [
            '0000000000000000',
            '0000000000000000',
            '0000077770000000',
            '0000777777000000',
            '0000766667000000',
            '0000616616000000',
            '0000066660000000',
            '0000016610000000',
            '0000066660000000',
            '0006161616000000',
            '0006666666000000',
            '0006161616000000',
            '0000066660000000',
            '0000066660000000',
            '0000060060000000',
            '0000000000000000',
        ],

        // --- GOLDEN CAPTAIN - All gold royal regalia ---
        legendary_golden: [
            '0000000000000000',
            '0000018881000000',
            '0000188888100000',
            '0011888888811000',
            '0000188881000000',
            '0000818118000000',
            '0000088880000000',
            '0000088880000000',
            '0000888888000000',
            '0008811188000000',
            '0008888888000000',
            '0008811188000000',
            '0000888888000000',
            '0000088880000000',
            '0000088088000000',
            '0000000000000000',
        ],

        // --- DEMON BUCCANEER - Red skin, horns, dark coat ---
        legendary_demon: [
            '0000000000000000',
            '0001000000010000',
            '0011700007710000',
            '0001777777710000',
            '0000777777000000',
            '0000787787000000',
            '0000077770000000',
            '0000017710000000',
            '0000022220000000',
            '0000272272000000',
            '0001277772100000',
            '0000272272000000',
            '0000022220000000',
            '0000022022000000',
            '0000022022000000',
            '0000000000000000',
        ],

        // --- KRAKEN LORD - Tentacle face, deep purple/green ---
        legendary_kraken: [
            '0000000000000000',
            '00000eeeeee00000',
            '0000eeeeeeee0000',
            '000beebeebeeb000',
            '0000eeeeeeee0000',
            '0000e8e88e8e0000',
            '0000eeeeeeee0000',
            '0000ebbbbbbe0000',
            '0000bbbbbbbb0000',
            '000bbeeeeebb0000',
            '0000bbbbbbbb0000',
            '0000bbbbbbbb0000',
            '000b00bb00b00000',
            '00b00b00b00b0000',
            '0b00b0000b00b000',
            '0000000000000000',
        ],

        // --- ROYAL PHANTOM - Crowned spectre in purple ---
        legendary_royal: [
            '0000000000000000',
            '0008080808080000',
            '0008888888880000',
            '0008666666680000',
            '0000666666000000',
            '0000616616000000',
            '0000066660000000',
            '0000018810000000',
            '00008eeeeee80000',
            '00008e8778e80000',
            '0008eeeeeeee8000',
            '0008eeeeeeee8000',
            '00008eeeeee80000',
            '00008e88e8000000',
            '0000080080000000',
            '0000000000000000',
        ],

    };

    // ===================================================
    // CHARACTER DEFINITIONS
    // Each character = base sprite + palette overrides
    // ===================================================

    const CHARACTERS = [
        // --- PIRATES ---
        // Captains — group links variants for the sub-picker
        { id: 'captain_m_light', base: 'captain_m', name: 'Captain', group: 'captain', category: 'Pirates', skin: 'light', hair: 'brown', primary: true, variantName: 'Driftwood' },
        { id: 'captain_m_med', base: 'captain_m', name: 'Captain', group: 'captain', category: 'Pirates', skin: 'medium', hair: 'black', variantName: 'Tideborn' },
        { id: 'captain_m_dark', base: 'captain_m', name: 'Captain', group: 'captain', category: 'Pirates', skin: 'dark', hair: 'black', variantName: 'Ironhull' },
        { id: 'captain_f_light', base: 'captain_f', name: 'Captain', group: 'captain', category: 'Pirates', skin: 'light', hair: 'red', variantName: 'Siren' },
        { id: 'captain_f_med', base: 'captain_f', name: 'Captain', group: 'captain', category: 'Pirates', skin: 'medium', hair: 'brown', variantName: 'Tempest' },
        { id: 'captain_f_dark', base: 'captain_f', name: 'Captain', group: 'captain', category: 'Pirates', skin: 'dark', hair: 'black', variantName: 'Stormcaller' },

        // First Mates
        { id: 'firstmate_m_light', base: 'firstmate_m', name: 'First Mate', group: 'firstmate', category: 'Pirates', skin: 'light', hair: 'brown', primary: true, variantName: 'Barnacle' },
        { id: 'firstmate_m_dark', base: 'firstmate_m', name: 'First Mate', group: 'firstmate', category: 'Pirates', skin: 'dark', hair: 'black', variantName: 'Whalebone' },
        { id: 'firstmate_f_light', base: 'firstmate_f', name: 'First Mate', group: 'firstmate', category: 'Pirates', skin: 'light', hair: 'blonde', variantName: 'Goldsail' },
        { id: 'firstmate_f_dark', base: 'firstmate_f', name: 'First Mate', group: 'firstmate', category: 'Pirates', skin: 'medium', hair: 'black', variantName: 'Coralreef' },

        // Deckhands
        { id: 'deckhand_light', base: 'deckhand', name: 'Deckhand', group: 'deckhand', category: 'Pirates', skin: 'light', hair: 'blonde', primary: true, variantName: 'Sandbar' },
        { id: 'deckhand_med', base: 'deckhand', name: 'Deckhand', group: 'deckhand', category: 'Pirates', skin: 'medium', hair: 'brown', variantName: 'Coppernail' },
        { id: 'deckhand_dark', base: 'deckhand', name: 'Deckhand', group: 'deckhand', category: 'Pirates', skin: 'dark', hair: 'black', variantName: 'Tarpitch' },

        // Gunners
        { id: 'gunner_light', base: 'gunner', name: 'Gunner', group: 'gunner', category: 'Pirates', skin: 'light', hair: 'brown', primary: true, variantName: 'Flintlock' },
        { id: 'gunner_dark', base: 'gunner', name: 'Gunner', group: 'gunner', category: 'Pirates', skin: 'dark', hair: 'black', variantName: 'Cannonsmoke' },

        // Navigator
        { id: 'navigator_light', base: 'navigator', name: 'Navigator', group: 'navigator', category: 'Pirates', skin: 'light', hair: 'grey', primary: true, variantName: 'Compass' },
        { id: 'navigator_dark', base: 'navigator', name: 'Navigator', group: 'navigator', category: 'Pirates', skin: 'medium', hair: 'brown', variantName: 'Tradewind' },

        // Quartermaster
        { id: 'quartermaster_light', base: 'quartermaster', name: 'Quartermaster', group: 'quartermaster', category: 'Pirates', skin: 'light', hair: 'brown', primary: true, variantName: 'Grogbarrel' },
        { id: 'quartermaster_dark', base: 'quartermaster', name: 'Quartermaster', group: 'quartermaster', category: 'Pirates', skin: 'dark', hair: 'grey', variantName: 'Salthaven' },

        // Lookout
        { id: 'lookout_light', base: 'lookout', name: 'Lookout', group: 'lookout', category: 'Pirates', skin: 'light', hair: 'brown', primary: true, variantName: "Crow's Nest" },
        { id: 'lookout_dark', base: 'lookout', name: 'Lookout', group: 'lookout', category: 'Pirates', skin: 'medium', hair: 'black', variantName: 'Nightwatch' },

        // --- MILITARY ---
        { id: 'eic_officer_light', base: 'eic_officer', name: 'EIC Officer', group: 'eic_officer', category: 'Military', skin: 'light', hair: 'brown', primary: true, variantName: 'Broadside' },
        { id: 'eic_officer_dark', base: 'eic_officer', name: 'EIC Officer', group: 'eic_officer', category: 'Military', skin: 'medium', hair: 'brown', variantName: 'Spicewind' },
        { id: 'redcoat_light', base: 'redcoat', name: 'Redcoat', group: 'redcoat', category: 'Military', skin: 'light', hair: 'brown', primary: true, variantName: 'Musketball' },
        { id: 'redcoat_dark', base: 'redcoat', name: 'Redcoat', group: 'redcoat', category: 'Military', skin: 'dark', hair: 'black', variantName: 'Powderkeg' },
        { id: 'naval_light', base: 'naval_officer', name: 'Naval Officer', group: 'naval', category: 'Military', skin: 'light', hair: 'brown', primary: true, variantName: 'Flagship' },
        { id: 'naval_dark', base: 'naval_officer', name: 'Naval Officer', group: 'naval', category: 'Military', skin: 'dark', hair: 'black', variantName: 'Deepwater' },

        // --- LEGENDARY SKINS (purchased with coins, each variant bought separately) ---
        { id: 'legendary_ghost',    base: 'legendary_ghost',    name: 'Ghost Captain',    category: 'Legendary', cost: 1500 },
        { id: 'legendary_skeleton', base: 'legendary_skeleton', name: 'Bone Pirate',      category: 'Legendary', cost: 2000 },
        { id: 'legendary_golden',   base: 'legendary_golden',   name: 'Golden Captain',   category: 'Legendary', cost: 3000 },
        { id: 'legendary_demon',    base: 'legendary_demon',    name: 'Demon Buccaneer',  category: 'Legendary', cost: 4000 },
        { id: 'legendary_kraken',   base: 'legendary_kraken',   name: 'Kraken Lord',      category: 'Legendary', cost: 5000 },
        { id: 'legendary_royal',    base: 'legendary_royal',    name: 'Royal Phantom',    category: 'Legendary', cost: 10000 },
    ];

    // === OWNED LEGENDARY SKINS (set by host page after auth) ===
    let ownedLegendarySkins = [];
    function setOwnedSkins(arr) {
        ownedLegendarySkins = Array.isArray(arr) ? arr.slice() : [];
        // If the currently equipped avatar is a legendary the user no longer
        // owns (e.g. after logout), revert to the default so they can't keep
        // showing it in-game.
        const sel = localStorage.getItem('pixelAvatar');
        const ch = sel && CHARACTERS.find(c => c.id === sel);
        if (ch && ch.category === 'Legendary' && ownedLegendarySkins.indexOf(sel) === -1) {
            localStorage.setItem('pixelAvatar', 'captain_m_light');
        }
        // Re-render any open pickers so locked/unlocked state updates immediately.
        ['m-pixel-char-picker', 'register-pixel-char-picker', 'login-pixel-char-picker'].forEach(id => {
            if (document.getElementById(id)) buildCharacterPicker(id);
        });
    }
    function isOwned(charId) {
        const ch = CHARACTERS.find(c => c.id === charId);
        if (!ch || ch.category !== 'Legendary') return true; // non-legendary always owned
        return ownedLegendarySkins.indexOf(charId) !== -1;
    }

    // === AI CHARACTER MAPPING (fixed assignments) ===
    const AI_CHARACTERS = {
        'Davy Jones': 'naval_dark',
        'Blackbeard': 'captain_m_dark',
        'Red Beard': 'firstmate_m_light',
        'Salty Pete': 'deckhand_med',
        'One-Eyed Willy': 'gunner_light',
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
            const fallbacks = ['captain_m_dark', 'firstmate_m_light', 'deckhand_dark', 'gunner_light', 'lookout_dark', 'eic_officer_light', 'redcoat_light', 'naval_dark'];
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

    // Get the primary (representative) characters — one per group
    function getPrimaryCharacters() {
        const seen = new Set();
        return CHARACTERS.filter(ch => {
            if (ch.primary && !seen.has(ch.group)) {
                seen.add(ch.group);
                return true;
            }
            return false;
        });
    }

    // Get all variants for a group
    function getGroupVariants(group) {
        return CHARACTERS.filter(ch => ch.group === group);
    }

    // Find which group the currently selected character belongs to
    function getSelectedGroup() {
        const sel = localStorage.getItem('pixelAvatar') || 'captain_m_light';
        const ch = CHARACTERS.find(c => c.id === sel);
        return ch ? ch.group : null;
    }

    function buildCharacterPicker(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const selected = localStorage.getItem('pixelAvatar') || 'captain_m_light';
        const selectedChar = CHARACTERS.find(c => c.id === selected);
        const selectedGroup = selectedChar ? selectedChar.group : null;

        const primaries = getPrimaryCharacters();

        // Single flat grid — regular characters then legendary skins inline.
        // Legendary tiles use the same grid so they fill any empty space on
        // the last row; visual differentiation comes from the .legendary class
        // (gold border) and a small separator before the first legendary tile.
        let html = '<div class="px-char-grid">';
        primaries.forEach(ch => {
            // Show selected variant's sprite if this group is selected
            let displayId = ch.id;
            if (ch.group === selectedGroup && selectedChar) {
                displayId = selectedChar.id;
            }
            const url = getSpriteDataURL(displayId, 3);
            const sel = ch.group === selectedGroup ? ' selected' : '';
            html += `<div class="px-char-option${sel}" data-group="${ch.group}" data-char-id="${displayId}"
                onclick="PixelAvatars.selectGroup('${ch.group}', '${containerId}')"
                ondblclick="PixelAvatars.openVariantPicker('${ch.group}', '${containerId}')">
                <img src="${url}" alt="${ch.name}">
                <div class="px-char-label">${ch.name}</div>
            </div>`;
        });

        // Legendary skins inline with the rest, after a small gold separator
        const legendary = CHARACTERS.filter(c => c.category === 'Legendary');
        if (legendary.length) {
            html += '<div class="px-legendary-sep" title="Legendary Skins">⭐</div>';
            legendary.forEach(ch => {
                const url = getSpriteDataURL(ch.id, 3);
                const owned = isOwned(ch.id);
                const sel = ch.id === selected ? ' selected' : '';
                const lockedCls = owned ? '' : ' locked';
                const label = owned ? ch.name : (ch.cost + 'c');
                html += `<div class="px-char-option legendary${lockedCls}${sel}" data-char-id="${ch.id}"
                    onclick="PixelAvatars.legendaryClick('${ch.id}', '${containerId}')"
                    ondblclick="PixelAvatars.legendaryDblClick('${ch.id}', '${containerId}')">
                    <img src="${url}" alt="${ch.name}">
                    <div class="px-char-label">${label}</div>
                </div>`;
            });
        }
        html += '</div>';

        // Variant sub-picker (hidden by default)
        html += '<div class="px-variant-picker hidden" id="px-variant-picker-' + containerId + '"></div>';

        container.innerHTML = html;
    }

    // Single-click on legendary: select if owned, otherwise no-op (double-click to buy)
    function legendaryClick(charId, containerId) {
        if (isOwned(charId)) {
            selectCharacter(charId, containerId);
        }
    }

    // Double-click on legendary: open purchase dialog if not owned
    function legendaryDblClick(charId, containerId) {
        if (isOwned(charId)) return; // already owned, no-op
        openPurchaseDialog(charId, containerId);
    }

    function openPurchaseDialog(charId, containerId) {
        const ch = CHARACTERS.find(c => c.id === charId);
        if (!ch || ch.category !== 'Legendary') return;

        // Remove any existing dialog
        const existing = document.getElementById('px-purchase-modal');
        if (existing) existing.remove();

        const url = getSpriteDataURL(charId, 5);
        const modal = document.createElement('div');
        modal.id = 'px-purchase-modal';
        modal.className = 'px-purchase-modal';
        modal.innerHTML = `
            <div class="px-purchase-card">
                <div class="px-purchase-title">⭐ Legendary Skin ⭐</div>
                <img class="px-purchase-sprite" src="${url}" alt="${ch.name}">
                <div class="px-purchase-name">${ch.name}</div>
                <div class="px-purchase-cost">Cost: <b>${ch.cost}</b> coins</div>
                <div class="px-purchase-actions">
                    <button class="px-purchase-cancel">Cancel</button>
                    <button class="px-purchase-confirm">Purchase</button>
                </div>
                <div class="px-purchase-msg" id="px-purchase-msg"></div>
            </div>`;
        document.body.appendChild(modal);

        modal.querySelector('.px-purchase-cancel').onclick = () => modal.remove();
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
        modal.querySelector('.px-purchase-confirm').onclick = () => {
            if (typeof window.onLegendaryPurchase === 'function') {
                window.onLegendaryPurchase(charId, ch.cost, containerId, modal);
            } else {
                const m = document.getElementById('px-purchase-msg');
                if (m) m.textContent = 'Log in to purchase legendary skins!';
            }
        };
    }

    function selectGroup(group, containerId) {
        // Single click: select the current variant for this group (or the primary)
        const selected = localStorage.getItem('pixelAvatar') || 'captain_m_light';
        const selectedChar = CHARACTERS.find(c => c.id === selected);

        // If already in this group, keep current variant
        if (selectedChar && selectedChar.group === group) return;

        // Otherwise select the primary variant
        const primary = CHARACTERS.find(c => c.group === group && c.primary);
        if (primary) {
            selectCharacter(primary.id, containerId);
        }
    }

    function openVariantPicker(group, containerId) {
        const picker = document.getElementById('px-variant-picker-' + containerId);
        if (!picker) return;

        const variants = getGroupVariants(group);
        const selected = localStorage.getItem('pixelAvatar') || 'captain_m_light';
        const groupName = variants[0]?.name || group;

        let html = `<div class="px-variant-header">
            <span>Choose ${groupName} Style</span>
            <button class="px-variant-close" onclick="PixelAvatars.closeVariantPicker('${containerId}')">&times;</button>
        </div>`;
        html += '<div class="px-variant-grid">';
        variants.forEach(ch => {
            const url = getSpriteDataURL(ch.id, 3);
            const sel = ch.id === selected ? ' selected' : '';
            const label = ch.variantName || ch.name;
            html += `<div class="px-char-option${sel}" data-char-id="${ch.id}"
                onclick="PixelAvatars.selectCharacter('${ch.id}', '${containerId}')">
                <img src="${url}" alt="${ch.name}">
                <div class="px-char-label">${label}</div>
            </div>`;
        });
        html += '</div>';

        picker.innerHTML = html;
        picker.classList.remove('hidden');
    }

    function closeVariantPicker(containerId) {
        const picker = document.getElementById('px-variant-picker-' + containerId);
        if (picker) picker.classList.add('hidden');
    }

    function selectCharacter(charId, containerId) {
        // Block selection of unowned legendary skins
        if (!isOwned(charId)) return;
        localStorage.setItem('pixelAvatar', charId);

        // Close variant picker
        closeVariantPicker(containerId);

        // Rebuild picker to reflect new selection
        buildCharacterPicker(containerId);

        // Update any visible pixel avatars
        if (typeof updateUI === 'function') {
            updateUI();
        }

        // Auto-save to account if logged in
        if (typeof onPixelAvatarSelected === 'function') {
            onPixelAvatarSelected(charId);
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
        selectGroup: selectGroup,
        selectCharacter: selectCharacter,
        openVariantPicker: openVariantPicker,
        closeVariantPicker: closeVariantPicker,
        preloadAll: preloadAll,
        setOwnedSkins: setOwnedSkins,
        isOwned: isOwned,
        legendaryClick: legendaryClick,
        legendaryDblClick: legendaryDblClick,
        openPurchaseDialog: openPurchaseDialog,
    };

    // Preload on next idle frame
    if (window.requestIdleCallback) {
        requestIdleCallback(preloadAll);
    } else {
        setTimeout(preloadAll, 100);
    }

})();
