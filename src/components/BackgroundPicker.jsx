import React from 'react';
import { backgroundMap } from '../constants';
import apiUnity from '../api_unity';

import zenless from '../assets/Zenless Zero.jpeg';
import rei from '../assets/rei.jpeg';
import reze from '../assets/reze.jpeg';

const imageMap = {
  'Zenless Zero': zenless,
  Rei: rei,
  Reze: reze,
};

export default function BackgroundPicker() {
  const keys = Object.keys(backgroundMap);

  return (
    <div className="fixed top-6 right-6 z-60 text-sm">
      <div className="group"> 
        {/* container grows on hover to reveal images (no popup) */}
        <div className="overflow-hidden rounded-lg bg-white/8 dark:bg-black/30 backdrop-blur-md border border-white/10 p-2 transform transition-all duration-200 group-hover:scale-105">
          <div className="flex items-center justify-center px-4 py-2 text-white font-medium">Backgrounds</div>

          <div className="mt-2 max-h-0 overflow-hidden transition-[max-height,opacity] duration-300 group-hover:max-h-screen group-hover:opacity-100 opacity-0">
            <div className="flex flex-col gap-3 px-2 py-2">
              {keys.map((k) => (
                <button
                  key={k}
                  onClick={() => {
                    const sprite = backgroundMap[k];
                    if (sprite) apiUnity.setBackground(sprite);
                  }}
                  className="flex flex-col items-center w-full select-auto bg-transparent rounded-md p-1 hover:bg-white/5 transition-colors"
                >
                  <div className="w-full h-28 overflow-hidden rounded-md">
                    <img src={imageMap[k]} alt={k} className="w-full h-full object-cover transform transition-transform duration-200 hover:scale-110" />
                  </div>
                  <div className="mt-2 text-center text-white text-sm w-full">{k}</div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
