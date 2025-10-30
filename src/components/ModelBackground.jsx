import React, { useEffect, useRef } from 'react';

export default function ModelBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

  const buildUrl = '/model/Build';
  // The exported files in this project are named model.* (not live2dweb.*)
  const loaderUrl = buildUrl + '/model.loader.js';

    const config = {
      arguments: [],
      dataUrl: buildUrl + '/model.data',
      frameworkUrl: buildUrl + '/model.framework.js',
      codeUrl: buildUrl + '/model.wasm',
      streamingAssetsUrl: 'StreamingAssets',
      companyName: 'DefaultCompany',
      productName: 'live2d',
      productVersion: '1.0',
      showBanner: () => {
        // Disable banner display
      }
    };

    // make canvas fill viewport
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';

    const script = document.createElement('script');
    script.src = loaderUrl;
    script.async = true;
    script.onload = () => {
      const createFn = window.createUnityInstance || window.createUnityInstanceAsync || window.createUnityInstanceFromLoader || window.createUnityInstance;
      if (typeof createFn !== 'function') {
        return;
      }
      createFn(canvas, config).then((unityInstance) => {
        window.__unityBgInstance = unityInstance;
      }).catch(() => {
        // Failed to create Unity instance
      });
    };

    document.body.appendChild(script);

    return () => {
      if (window.__unityBgInstance && window.__unityBgInstance.Quit) {
        window.__unityBgInstance.Quit().catch(()=>{});
        delete window.__unityBgInstance;
      }
      script.remove();
    };
  }, []);

  // Tailwind utility classes: fixed, inset-0, -z-10 to put behind content, pointer-events-none
  return (
    <div className="fixed inset-0 -z-10 pointer-events-none">
      <canvas id="unity-canvas" ref={canvasRef} tabIndex={-1} className="w-screen h-screen block"></canvas>
    </div>
  );
}
