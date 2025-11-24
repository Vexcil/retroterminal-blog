---
layout: default
title: Building a Fully Automated Watering System for My Grow Tent
---

I recently finished a major upgrade to my indoor grow setup: a fully automated watering system controlled from my phone. What started as a simple pump project turned into a complete end-to-end redesign of how I store, prepare and deliver water inside my setup. Below is a full breakdown of the system, its components, the workflow, and the future expansion plans.

## The Environment

The core of this project is a Vivosun 4x4x7 grow tent. Next to it sits a heavy-duty black epoxy wire shelving rack that holds two stacked 27-gallon totes. These act as my water-storage and nutrient-mixing stations. The Pi and IoT relay box sit on the same rack, safely elevated and isolated from moisture.

## Water Storage and Conditioning

The top 27-gallon tote holds plain tap water. I divert water directly from my washing machine’s cold-water intake. Once filled, the water sits for roughly two days. This naturally dechlorinates it before use.

To move water between the totes, the top one has a self-sealing rain-barrel spigot installed on the underside. When opened, it drains into the lower tote. The bottom tote is where I mix in pH up/down and any nutrients.

The pump sits inside this lower tote. Power to the pump goes through an IoT relay box which I control through a secure login on retroterminal.net. I won’t cover the connection paths publicly for obvious reasons. The important part is that the pump can be turned on or off from my phone.

## Irrigation Line Layout

From the pump, the water flow follows this chain:

1. **1/2 inch mainline from pump**
2. **1/2 inch check valve** to stop backflow
3. **Sentry fine-mesh strainer** to catch debris
4. **1/2 inch run into the tent**

Inside the tent, the 1/2 inch line terminates into three **1/2 inch to 1/4 inch tee reducers**. These supply three branches.

Each 1/4 inch line then goes through:

• A **1/4 inch check valve**
• A transition to **1/8 inch clear tubing**
• A **halo ring** at the end

The clear 1/8 inch line makes it easy to see clogs or sediment buildup.

Once nutrients and pH adjustments are made, I simply enable the pump. The tent is now fully controllable from my phone: lights, humidity, airflow, temperature, and now water. The plants get exactly what they need, when they need it.

## Tubing and Fitting Challenges

One of the hardest parts of this build was dealing with mismatched tubing tolerances. “Nominal” sizes aren’t universal. A lot of tubing simply didn’t fit the fittings even though the sizes technically matched.

The reliable fix was heat and lubrication:

• Warm the tubing with a hot-air gun
• Add a small amount of soap
• Press it over the barb

Once it cools, the fit is rock-solid. Nearly impossible to remove without cutting.

## Planned Expansion

Next, I’m adding a second full watering rail using larger halo rings. To do that:

1. Cut the current 1/2 inch line before the 1/2-to-1/4 tee cluster
2. Insert a **1/2 inch to 1/2 inch tee**
3. Run a second 1/2 inch line parallel to the original
4. Add check valves at both the start and end of each halo run
5. Choose between small and large halo systems by toggling valves, not re-fitting lines

This keeps the system modular and avoids redoing all the small 1/8 inch lines.

## Future Automation

After this upcoming grow cycle, I’m adding sensors:

• **Soil moisture sensors** for real-time plant feedback
• **Water pH and EC sensors** inside the bottom tote
• **A low-water safety cutoff** to protect the pump
• **Automated pH dosers** that adjust pH based on the sensor readings
• Historical logs and dashboards for tracking each run

Once those pieces are integrated, the system will be almost entirely autonomous.

---

This project has already made my grow more consistent and far easier to manage. Water conditioning, nutrient mixing, and delivery are now controlled, repeatable and remotely adjustable. With the next set of upgrades, the entire tent will move closer to true hands-off operation.
