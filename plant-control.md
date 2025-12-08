---
layout: default
title: Plant Pump Control
permalink: /plant-control/
---

<section class="hero">
  <h2>Plant Pump Control</h2>
  <p>
    Internal controller for the watering relay on node
    <code style="color:#4ecaff;font-size: 20px;vertical-align: 1px;">water</code>.
  </p>
</section>

<section class="services">
  <h2>Control Panel</h2>

  <div class="control-wrapper">
    <iframe
      src="https://plant.retroterminal.net/"
      class="control-frame">
    </iframe>
  </div>
</section>

<style>
  .control-wrapper {
    width: 100%;
    max-width: 1200px;
    margin: 2rem auto;
    border: 2px solid #0f0;
    background: #000;
    padding: 0;
  }

  .control-frame {
    width: 100%;
    height: 75vh; /* fills most of the viewport height */
    border: none;
    background: #000;
  }

  @media (max-width: 800px) {
    .control-frame {
      height: 60vh; /* a bit shorter on phones */
    }
  }
</style>
