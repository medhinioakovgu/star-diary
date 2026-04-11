import React from 'react';
import { Dimensions, StyleSheet, TouchableOpacity, View } from 'react-native';
import { SvgXml } from 'react-native-svg';

interface DiaryCoverProps {
  onOpen: () => void;
}

const svgXml = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 390 844" width="390" height="844">
  <defs>
    <!-- Background -->
    <linearGradient id="bgGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#F2F0EB"/>
      <stop offset="85%" stop-color="#F2F0EB"/>
      <stop offset="100%" stop-color="#E8E4DC" stop-opacity="0.6"/>
    </linearGradient>
    <!-- Gold gradient horizontal -->
    <linearGradient id="goldH" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#C9A84C" stop-opacity="0"/>
      <stop offset="20%" stop-color="#C9A84C"/>
      <stop offset="50%" stop-color="#F0D080"/>
      <stop offset="80%" stop-color="#C9A84C"/>
      <stop offset="100%" stop-color="#C9A84C" stop-opacity="0"/>
    </linearGradient>
    <!-- Gold gradient for ornaments -->
    <linearGradient id="goldOrnTL" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#F0D080"/>
      <stop offset="60%" stop-color="#C9A84C"/>
      <stop offset="100%" stop-color="#A8832A"/>
    </linearGradient>
    <linearGradient id="goldOrnTR" x1="1" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F0D080"/>
      <stop offset="60%" stop-color="#C9A84C"/>
      <stop offset="100%" stop-color="#A8832A"/>
    </linearGradient>
    <linearGradient id="goldOrnBL" x1="0" y1="1" x2="1" y2="0">
      <stop offset="0%" stop-color="#F0D080"/>
      <stop offset="60%" stop-color="#C9A84C"/>
      <stop offset="100%" stop-color="#A8832A"/>
    </linearGradient>
    <linearGradient id="goldOrnBR" x1="1" y1="1" x2="0" y2="0">
      <stop offset="0%" stop-color="#F0D080"/>
      <stop offset="60%" stop-color="#C9A84C"/>
      <stop offset="100%" stop-color="#A8832A"/>
    </linearGradient>
    <!-- Right edge shadow -->
    <linearGradient id="shadowRight" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="#8B7355" stop-opacity="0"/>
      <stop offset="100%" stop-color="#8B7355" stop-opacity="0.18"/>
    </linearGradient>
  </defs>

  <!-- Background -->
  <rect width="390" height="844" fill="url(#bgGrad)"/>

  <!-- Right edge book shadow -->
  <rect x="340" y="0" width="50" height="844" fill="url(#shadowRight)"/>

  <!-- ===================== TOP LEFT CORNER ORNAMENT ===================== -->
  <g transform="translate(0,0)" stroke="url(#goldOrnTL)" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <!-- Main sweeping vine arms -->
    <path d="M 5,5 Q 30,8 55,5 Q 80,2 100,8" stroke-width="1.2"/>
    <path d="M 5,5 Q 8,30 5,55 Q 2,80 8,100" stroke-width="1.2"/>
    <!-- Diagonal flourish -->
    <path d="M 5,5 Q 35,35 65,75 Q 75,88 70,100" stroke-width="0.9"/>
    <path d="M 5,5 Q 35,35 75,65 Q 88,75 100,70" stroke-width="0.9"/>
    <!-- Top edge curls and petals -->
    <path d="M 20,5 Q 22,15 18,22 Q 14,28 20,30 Q 26,28 24,22 Q 22,15 26,5" stroke-width="0.7"/>
    <path d="M 40,4 Q 42,12 38,18 Q 34,24 40,25 Q 46,24 44,18 Q 42,12 46,4" stroke-width="0.7"/>
    <path d="M 60,5 Q 62,14 58,20 Q 54,26 60,27 Q 66,26 64,20 Q 62,14 66,6" stroke-width="0.7"/>
    <path d="M 78,7 Q 80,15 76,21 Q 72,26 78,27 Q 84,25 82,19 Q 80,13 84,8" stroke-width="0.7"/>
    <!-- Left edge curls and petals -->
    <path d="M 5,20 Q 15,22 22,18 Q 28,14 30,20 Q 28,26 22,24 Q 15,22 5,26" stroke-width="0.7"/>
    <path d="M 4,40 Q 12,42 18,38 Q 24,34 25,40 Q 24,46 18,44 Q 12,42 4,46" stroke-width="0.7"/>
    <path d="M 5,60 Q 14,62 20,58 Q 26,54 27,60 Q 26,66 20,64 Q 14,62 6,66" stroke-width="0.7"/>
    <path d="M 7,78 Q 15,80 21,76 Q 27,72 27,78 Q 25,84 19,82 Q 13,80 8,84" stroke-width="0.7"/>
    <!-- Small swirls along diagonal -->
    <path d="M 25,25 Q 30,20 35,25 Q 30,30 25,25" stroke-width="0.6"/>
    <path d="M 42,42 Q 48,37 53,42 Q 48,47 42,42" stroke-width="0.6"/>
    <path d="M 55,60 Q 60,55 65,60 Q 60,65 55,60" stroke-width="0.6"/>
    <!-- Fine detail lines -->
    <path d="M 15,10 Q 12,18 15,25 Q 18,18 15,10" stroke-width="0.5"/>
    <path d="M 10,15 Q 18,12 25,15 Q 18,18 10,15" stroke-width="0.5"/>
    <path d="M 30,15 Q 27,22 30,28" stroke-width="0.5"/>
    <path d="M 15,30 Q 22,27 28,30" stroke-width="0.5"/>
    <!-- Leaf-like petal clusters -->
    <path d="M 48,12 Q 53,8 56,14 Q 51,18 48,12" stroke-width="0.6" fill="url(#goldOrnTL)" fill-opacity="0.15"/>
    <path d="M 56,14 Q 62,10 64,16 Q 58,20 56,14" stroke-width="0.6" fill="url(#goldOrnTL)" fill-opacity="0.15"/>
    <path d="M 12,48 Q 8,53 14,56 Q 18,51 12,48" stroke-width="0.6" fill="url(#goldOrnTL)" fill-opacity="0.15"/>
    <path d="M 14,56 Q 10,62 16,64 Q 20,58 14,56" stroke-width="0.6" fill="url(#goldOrnTL)" fill-opacity="0.15"/>
    <!-- Corner dot/rosette -->
    <circle cx="12" cy="12" r="3" stroke-width="0.8" fill="url(#goldOrnTL)" fill-opacity="0.3"/>
    <circle cx="12" cy="12" r="5" stroke-width="0.5"/>
    <circle cx="12" cy="12" r="7" stroke-width="0.4" stroke-opacity="0.5"/>
    <!-- Extra fine tendrils -->
    <path d="M 35,8 Q 38,16 34,24" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 50,6 Q 53,14 49,22" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 8,35 Q 16,38 24,34" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 6,50 Q 14,53 22,49" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 70,9 Q 74,17 70,24" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 90,10 Q 93,18 89,25" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 9,70 Q 17,74 24,70" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 10,90 Q 18,93 25,89" stroke-width="0.45" stroke-opacity="0.7"/>
  </g>

  <!-- ===================== TOP RIGHT CORNER ORNAMENT ===================== -->
  <g transform="translate(390,0) scale(-1,1)" stroke="url(#goldOrnTR)" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 5,5 Q 30,8 55,5 Q 80,2 100,8" stroke-width="1.2"/>
    <path d="M 5,5 Q 8,30 5,55 Q 2,80 8,100" stroke-width="1.2"/>
    <path d="M 5,5 Q 35,35 65,75 Q 75,88 70,100" stroke-width="0.9"/>
    <path d="M 5,5 Q 35,35 75,65 Q 88,75 100,70" stroke-width="0.9"/>
    <path d="M 20,5 Q 22,15 18,22 Q 14,28 20,30 Q 26,28 24,22 Q 22,15 26,5" stroke-width="0.7"/>
    <path d="M 40,4 Q 42,12 38,18 Q 34,24 40,25 Q 46,24 44,18 Q 42,12 46,4" stroke-width="0.7"/>
    <path d="M 60,5 Q 62,14 58,20 Q 54,26 60,27 Q 66,26 64,20 Q 62,14 66,6" stroke-width="0.7"/>
    <path d="M 78,7 Q 80,15 76,21 Q 72,26 78,27 Q 84,25 82,19 Q 80,13 84,8" stroke-width="0.7"/>
    <path d="M 5,20 Q 15,22 22,18 Q 28,14 30,20 Q 28,26 22,24 Q 15,22 5,26" stroke-width="0.7"/>
    <path d="M 4,40 Q 12,42 18,38 Q 24,34 25,40 Q 24,46 18,44 Q 12,42 4,46" stroke-width="0.7"/>
    <path d="M 5,60 Q 14,62 20,58 Q 26,54 27,60 Q 26,66 20,64 Q 14,62 6,66" stroke-width="0.7"/>
    <path d="M 7,78 Q 15,80 21,76 Q 27,72 27,78 Q 25,84 19,82 Q 13,80 8,84" stroke-width="0.7"/>
    <path d="M 25,25 Q 30,20 35,25 Q 30,30 25,25" stroke-width="0.6"/>
    <path d="M 42,42 Q 48,37 53,42 Q 48,47 42,42" stroke-width="0.6"/>
    <path d="M 55,60 Q 60,55 65,60 Q 60,65 55,60" stroke-width="0.6"/>
    <path d="M 15,10 Q 12,18 15,25 Q 18,18 15,10" stroke-width="0.5"/>
    <path d="M 10,15 Q 18,12 25,15 Q 18,18 10,15" stroke-width="0.5"/>
    <path d="M 30,15 Q 27,22 30,28" stroke-width="0.5"/>
    <path d="M 15,30 Q 22,27 28,30" stroke-width="0.5"/>
    <path d="M 48,12 Q 53,8 56,14 Q 51,18 48,12" stroke-width="0.6" fill="url(#goldOrnTR)" fill-opacity="0.15"/>
    <path d="M 56,14 Q 62,10 64,16 Q 58,20 56,14" stroke-width="0.6" fill="url(#goldOrnTR)" fill-opacity="0.15"/>
    <path d="M 12,48 Q 8,53 14,56 Q 18,51 12,48" stroke-width="0.6" fill="url(#goldOrnTR)" fill-opacity="0.15"/>
    <path d="M 14,56 Q 10,62 16,64 Q 20,58 14,56" stroke-width="0.6" fill="url(#goldOrnTR)" fill-opacity="0.15"/>
    <circle cx="12" cy="12" r="3" stroke-width="0.8" fill="url(#goldOrnTR)" fill-opacity="0.3"/>
    <circle cx="12" cy="12" r="5" stroke-width="0.5"/>
    <circle cx="12" cy="12" r="7" stroke-width="0.4" stroke-opacity="0.5"/>
    <path d="M 35,8 Q 38,16 34,24" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 50,6 Q 53,14 49,22" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 8,35 Q 16,38 24,34" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 6,50 Q 14,53 22,49" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 70,9 Q 74,17 70,24" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 90,10 Q 93,18 89,25" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 9,70 Q 17,74 24,70" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 10,90 Q 18,93 25,89" stroke-width="0.45" stroke-opacity="0.7"/>
  </g>

  <!-- ===================== BOTTOM LEFT CORNER ORNAMENT ===================== -->
  <g transform="translate(0,844) scale(1,-1)" stroke="url(#goldOrnBL)" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 5,5 Q 30,8 55,5 Q 80,2 100,8" stroke-width="1.2"/>
    <path d="M 5,5 Q 8,30 5,55 Q 2,80 8,100" stroke-width="1.2"/>
    <path d="M 5,5 Q 35,35 65,75 Q 75,88 70,100" stroke-width="0.9"/>
    <path d="M 5,5 Q 35,35 75,65 Q 88,75 100,70" stroke-width="0.9"/>
    <path d="M 20,5 Q 22,15 18,22 Q 14,28 20,30 Q 26,28 24,22 Q 22,15 26,5" stroke-width="0.7"/>
    <path d="M 40,4 Q 42,12 38,18 Q 34,24 40,25 Q 46,24 44,18 Q 42,12 46,4" stroke-width="0.7"/>
    <path d="M 60,5 Q 62,14 58,20 Q 54,26 60,27 Q 66,26 64,20 Q 62,14 66,6" stroke-width="0.7"/>
    <path d="M 78,7 Q 80,15 76,21 Q 72,26 78,27 Q 84,25 82,19 Q 80,13 84,8" stroke-width="0.7"/>
    <path d="M 5,20 Q 15,22 22,18 Q 28,14 30,20 Q 28,26 22,24 Q 15,22 5,26" stroke-width="0.7"/>
    <path d="M 4,40 Q 12,42 18,38 Q 24,34 25,40 Q 24,46 18,44 Q 12,42 4,46" stroke-width="0.7"/>
    <path d="M 5,60 Q 14,62 20,58 Q 26,54 27,60 Q 26,66 20,64 Q 14,62 6,66" stroke-width="0.7"/>
    <path d="M 7,78 Q 15,80 21,76 Q 27,72 27,78 Q 25,84 19,82 Q 13,80 8,84" stroke-width="0.7"/>
    <path d="M 25,25 Q 30,20 35,25 Q 30,30 25,25" stroke-width="0.6"/>
    <path d="M 42,42 Q 48,37 53,42 Q 48,47 42,42" stroke-width="0.6"/>
    <path d="M 55,60 Q 60,55 65,60 Q 60,65 55,60" stroke-width="0.6"/>
    <path d="M 15,10 Q 12,18 15,25 Q 18,18 15,10" stroke-width="0.5"/>
    <path d="M 10,15 Q 18,12 25,15 Q 18,18 10,15" stroke-width="0.5"/>
    <path d="M 30,15 Q 27,22 30,28" stroke-width="0.5"/>
    <path d="M 15,30 Q 22,27 28,30" stroke-width="0.5"/>
    <path d="M 48,12 Q 53,8 56,14 Q 51,18 48,12" stroke-width="0.6" fill="url(#goldOrnBL)" fill-opacity="0.15"/>
    <path d="M 56,14 Q 62,10 64,16 Q 58,20 56,14" stroke-width="0.6" fill="url(#goldOrnBL)" fill-opacity="0.15"/>
    <path d="M 12,48 Q 8,53 14,56 Q 18,51 12,48" stroke-width="0.6" fill="url(#goldOrnBL)" fill-opacity="0.15"/>
    <path d="M 14,56 Q 10,62 16,64 Q 20,58 14,56" stroke-width="0.6" fill="url(#goldOrnBL)" fill-opacity="0.15"/>
    <circle cx="12" cy="12" r="3" stroke-width="0.8" fill="url(#goldOrnBL)" fill-opacity="0.3"/>
    <circle cx="12" cy="12" r="5" stroke-width="0.5"/>
    <circle cx="12" cy="12" r="7" stroke-width="0.4" stroke-opacity="0.5"/>
    <path d="M 35,8 Q 38,16 34,24" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 50,6 Q 53,14 49,22" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 8,35 Q 16,38 24,34" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 6,50 Q 14,53 22,49" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 70,9 Q 74,17 70,24" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 90,10 Q 93,18 89,25" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 9,70 Q 17,74 24,70" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 10,90 Q 18,93 25,89" stroke-width="0.45" stroke-opacity="0.7"/>
  </g>

  <!-- ===================== BOTTOM RIGHT CORNER ORNAMENT ===================== -->
  <g transform="translate(390,844) scale(-1,-1)" stroke="url(#goldOrnBR)" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 5,5 Q 30,8 55,5 Q 80,2 100,8" stroke-width="1.2"/>
    <path d="M 5,5 Q 8,30 5,55 Q 2,80 8,100" stroke-width="1.2"/>
    <path d="M 5,5 Q 35,35 65,75 Q 75,88 70,100" stroke-width="0.9"/>
    <path d="M 5,5 Q 35,35 75,65 Q 88,75 100,70" stroke-width="0.9"/>
    <path d="M 20,5 Q 22,15 18,22 Q 14,28 20,30 Q 26,28 24,22 Q 22,15 26,5" stroke-width="0.7"/>
    <path d="M 40,4 Q 42,12 38,18 Q 34,24 40,25 Q 46,24 44,18 Q 42,12 46,4" stroke-width="0.7"/>
    <path d="M 60,5 Q 62,14 58,20 Q 54,26 60,27 Q 66,26 64,20 Q 62,14 66,6" stroke-width="0.7"/>
    <path d="M 78,7 Q 80,15 76,21 Q 72,26 78,27 Q 84,25 82,19 Q 80,13 84,8" stroke-width="0.7"/>
    <path d="M 5,20 Q 15,22 22,18 Q 28,14 30,20 Q 28,26 22,24 Q 15,22 5,26" stroke-width="0.7"/>
    <path d="M 4,40 Q 12,42 18,38 Q 24,34 25,40 Q 24,46 18,44 Q 12,42 4,46" stroke-width="0.7"/>
    <path d="M 5,60 Q 14,62 20,58 Q 26,54 27,60 Q 26,66 20,64 Q 14,62 6,66" stroke-width="0.7"/>
    <path d="M 7,78 Q 15,80 21,76 Q 27,72 27,78 Q 25,84 19,82 Q 13,80 8,84" stroke-width="0.7"/>
    <path d="M 25,25 Q 30,20 35,25 Q 30,30 25,25" stroke-width="0.6"/>
    <path d="M 42,42 Q 48,37 53,42 Q 48,47 42,42" stroke-width="0.6"/>
    <path d="M 55,60 Q 60,55 65,60 Q 60,65 55,60" stroke-width="0.6"/>
    <path d="M 15,10 Q 12,18 15,25 Q 18,18 15,10" stroke-width="0.5"/>
    <path d="M 10,15 Q 18,12 25,15 Q 18,18 10,15" stroke-width="0.5"/>
    <path d="M 30,15 Q 27,22 30,28" stroke-width="0.5"/>
    <path d="M 15,30 Q 22,27 28,30" stroke-width="0.5"/>
    <path d="M 48,12 Q 53,8 56,14 Q 51,18 48,12" stroke-width="0.6" fill="url(#goldOrnBR)" fill-opacity="0.15"/>
    <path d="M 56,14 Q 62,10 64,16 Q 58,20 56,14" stroke-width="0.6" fill="url(#goldOrnBR)" fill-opacity="0.15"/>
    <path d="M 12,48 Q 8,53 14,56 Q 18,51 12,48" stroke-width="0.6" fill="url(#goldOrnBR)" fill-opacity="0.15"/>
    <path d="M 14,56 Q 10,62 16,64 Q 20,58 14,56" stroke-width="0.6" fill="url(#goldOrnBR)" fill-opacity="0.15"/>
    <circle cx="12" cy="12" r="3" stroke-width="0.8" fill="url(#goldOrnBR)" fill-opacity="0.3"/>
    <circle cx="12" cy="12" r="5" stroke-width="0.5"/>
    <circle cx="12" cy="12" r="7" stroke-width="0.4" stroke-opacity="0.5"/>
    <path d="M 35,8 Q 38,16 34,24" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 50,6 Q 53,14 49,22" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 8,35 Q 16,38 24,34" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 6,50 Q 14,53 22,49" stroke-width="0.45" stroke-opacity="0.8"/>
    <path d="M 70,9 Q 74,17 70,24" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 90,10 Q 93,18 89,25" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 9,70 Q 17,74 24,70" stroke-width="0.45" stroke-opacity="0.7"/>
    <path d="M 10,90 Q 18,93 25,89" stroke-width="0.45" stroke-opacity="0.7"/>
  </g>

  <!-- ===================== CENTER LOGO STACK ===================== -->
  <!-- Vertically centered around y=422 -->
  <!-- Total stack height estimate: star(80) + gap(18) + STAR(48) + gap(16) + rule(1) + gap(12) + AIDIARY(14) + gap(10) + goldline(1) + gap(10) + 2026(12) = ~222px -->
  <!-- Center at y=422, so stack starts at y=311 -->

  <g transform="translate(195, 310)">

    <!-- 1. COMPASS STAR â 4-pointed, elongated vertical -->
    <!-- Top spike, bottom spike, left arm, right arm -->
    <!-- Center at (0,0), drawn relative -->
    <g id="compassStar" fill="none" stroke="#2B2B2B" stroke-width="0.7" stroke-linecap="round" stroke-linejoin="round">
      <!-- Main 4-point star outline â elongated top/bottom, shorter left/right -->
      <!-- Top spike: tall -->
      <path d="M 0,-60 C 3,-30 8,-18 12,-8 L 0,0 L -12,-8 C -8,-18 -3,-30 0,-60 Z" stroke-width="0.6"/>
      <!-- Bottom spike: tall -->
      <path d="M 0,60 C 3,30 8,18 12,8 L 0,0 L -12,8 C -8,18 -3,30 0,60 Z" stroke-width="0.6"/>
      <!-- Right arm: shorter -->
      <path d="M 32,0 C 18,3 10,6 6,10 L 0,0 L 6,-10 C 10,-6 18,-3 32,0 Z" stroke-width="0.6"/>
      <!-- Left arm: shorter -->
      <path d="M -32,0 C -18,3 -10,6 -6,10 L 0,0 L -6,-10 C -10,-6 -18,-3 -32,0 Z" stroke-width="0.6"/>
      <!-- Hairline center diamond outline -->
      <polygon points="0,-12 6,0 0,12 -6,0" stroke-width="0.5" fill="#F2F0EB"/>
      <!-- Fine inner detail lines on top spike -->
      <path d="M 0,-60 L 0,-12" stroke-width="0.35" stroke-opacity="0.5"/>
      <!-- Fine inner detail lines on bottom spike -->
      <path d="M 0,60 L 0,12" stroke-width="0.35" stroke-opacity="0.5"/>
      <!-- Fine inner detail on right arm -->
      <path d="M 32,0 L 6,0" stroke-width="0.35" stroke-opacity="0.5"/>
      <!-- Fine inner detail on left arm -->
      <path d="M -32,0 L -6,0" stroke-width="0.35" stroke-opacity="0.5"/>
      <!-- Tiny center dot -->
      <circle cx="0" cy="0" r="1.5" fill="#2B2B2B" stroke="none"/>
      <!-- Hairline outer guide -->
      <line x1="0" y1="-62" x2="0" y2="-58" stroke-width="0.4" stroke-opacity="0.3"/>
      <line x1="0" y1="58" x2="0" y2="62" stroke-width="0.4" stroke-opacity="0.3"/>
      <line x1="-34" y1="0" x2="-30" y2="0" stroke-width="0.4" stroke-opacity="0.3"/>
      <line x1="30" y1="0" x2="34" y2="0" stroke-width="0.4" stroke-opacity="0.3"/>
    </g>

    <!-- 2. "STAR" in large serif, wide-spaced â using text with letter-spacing -->
    <!-- y offset from center: 60 (bottom of star) + 18 gap + 38 (baseline) = 116 -->
    <text
      x="0"
      y="116"
      text-anchor="middle"
      font-family="PlayfairDisplay-Regular"
      font-size="46"
      font-weight="bold"
      fill="#2B2B2B"
      letter-spacing="18"
      xml:space="preserve">STAR</text>

    <!-- 3. Thin hairline rule -->
    <!-- y = 116 + 16 = 132 -->
    <line x1="-75" y1="136" x2="75" y2="136" stroke="#2B2B2B" stroke-width="0.5"/>

    <!-- 4. "AI DIARY" in small caps widely spaced -->
    <!-- y = 136 + 18 = 154 -->
    <text
      x="0"
      y="156"
      text-anchor="middle"
      font-family="PlayfairDisplay-Regular"
      font-size="9.5"
      font-weight="300"
      fill="#2B2B2B"
      letter-spacing="7"
      opacity="0.85"
      xml:space="preserve">AI  DIARY</text>

    <!-- 5. Gold gradient horizontal line -->
    <!-- y = 156 + 14 = 170 -->
    <line x1="-80" y1="174" x2="80" y2="174" stroke="url(#goldH)" stroke-width="1"/>

    <!-- 6. "2026 EDITION" faint small caps -->
    <!-- y = 174 + 14 = 188 -->
    <text
      x="0"
      y="192"
      text-anchor="middle"
      font-family="Georgia, 'Times New Roman', Times, serif"
      font-size="8"
      font-weight="300"
      fill="#2B2B2B"
      letter-spacing="5"
      opacity="0.45"
      xml:space="preserve">2026  EDITION</text>

  </g>

</svg>
`;

export const DiaryCover: React.FC<DiaryCoverProps> = ({ onOpen }) => {
  const { width, height } = Dimensions.get('window');

  return (
    <View style={styles.wrapper}>
      <SvgXml xml={svgXml} width={width} height={height} />
      <View style={styles.pageFlipContainer}>
        <TouchableOpacity style={styles.pageFlipTouchArea} onPress={onOpen} activeOpacity={0.8}>
          <View style={styles.hitArea} />
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    flex: 1,
    width: '100%',
    height: '100%',
    backgroundColor: '#F2F0EB',
    borderLeftWidth: 10,
    borderLeftColor: '#D8D5CF',
    shadowColor: '#000',
    shadowOpacity: 0.2,
    shadowRadius: 15,
    shadowOffset: { width: 0, height: 8 },
    elevation: 8,
    overflow: 'visible',
  },
  pageFlipContainer: {
    position: 'absolute',
    top: 0,
    right: 0,
    width: 80,
    height: '100%',
  },
  pageFlipTouchArea: {
    flex: 1,
  },
  hitArea: {
    flex: 1,
  },
});
