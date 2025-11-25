---
layout: default
title: Building a Fully Automated Watering System for My Grow Tent
---

I recently finished a major upgrade to my indoor grow setup: a fully automated watering system controlled from my phone. What started as a simple pump project turned into a complete end-to-end redesign of how I store, prepare and deliver water inside my setup. Below is a full breakdown of the system, its components, the workflow, and the future expansion plans.

## The Environment

The core of this project is a Vivosun 4'x4x'7' grow tent. Next to it sits a heavy-duty black epoxy wire shelving rack that holds two stacked 27-gallon totes. These act as my water-storage and nutrient-mixing stations. The Pi and IoT relay box sit on the same rack one level up, safely elevated and isolated from moisture.
![Mainline and Netting]({{ "/assets/posts/blog-water-automation/mainline-and-netting.jpg" | relative_url }})

## Water Storage and Conditioning

![Two Tote System]({{ "/assets/posts/blog-water-automation/two-tote-system.jpg" | relative_url }})

The top 27-gallon tote holds plain tap water. I divert water directly from my washing machine’s cold-water intake. Once filled, the water sits for roughly two days. This naturally dechlorinates it before use.

To move water between the totes, the top one has a self-sealing rain-barrel spigot installed on the underside. When opened, it drains into the lower tote. The bottom tote is where I mix in pH up/down and any nutrients.

The pump sits inside this lower tote. Power to the pump goes through an IoT relay box which I control through a secure portal on any web browser. I won’t cover the connection paths publicly for obvious reasons. The important part is that the pump can be turned on or off from my phone anywhere in the world.

![IoT Relay Box]({{ "/assets/posts/blog-water-automation/iot-relay.jpg" | relative_url }})
![Raspberry Pi Zero 2W]({{ "/assets/posts/blog-water-automation/pi-water-closeup.jpg" | relative_url }})

## Irrigation Line Layout

From the pump, the water flow follows this chain:

1. **1/2 inch mainline from pump**
2. **1/2 inch check valve** to stop backflow
3. **Sentry fine-mesh strainer** to catch debris
4. **1/2 inch run into the tent**

Inside the tent, the 1/2 inch line terminates into three **1/2 inch to 1/4 inch tee reducers**. These supply three branches.

![Tubing affixed to netting]({{ "/assets/posts/blog-water-automation/halftoquarter.jpg" | relative_url }})

Each 1/4 inch line then goes through:

• A **1/4 inch check valve**
• A transition to **1/8 inch clear tubing**
• A **halo ring** at the end

The clear 1/8 inch line makes it easy to see clogs or sediment buildup.

![Clear Tube Connection]({{ "/assets/posts/blog-water-automation/clear-tube-connection.jpg" | relative_url }})

Once nutrients and pH adjustments are made, I simply enable the pump. The tent is now fully controllable from my phone: lights, humidity, airflow, temperature, and now water. The plants get exactly what they need, when they need it.

![Phone View]({{ "/assets/posts/blog-water-automation/Screenshot_20251123_165734_Firefox.jpg" | relative_url }})

## Tubing and Fitting Challenges

One of the hardest parts of this build was dealing with mismatched tubing tolerances. “Nominal” sizes aren’t universal. A lot of tubing simply didn’t fit the fittings even though the sizes technically matched.

The reliable fix was heat and lubrication:

• Warm the tubing with a hot-air gun
• Add a small amount of soap
• Press it over the barb

Once it cools, the fit is rock-solid. Nearly impossible to remove without cutting.

![Tent No Plant]({{ "/assets/posts/blog-water-automation/finished-tent-no-plant.jpg" | relative_url }})

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

![Complete Wire Shelving Unit]({{ "/assets/posts/blog-water-automation/wire-rack-complete.jpg" | relative_url }})
![Complete tent - for now]({{ "/assets/posts/blog-water-automation/finished-tent.jpg" | relative_url }})
