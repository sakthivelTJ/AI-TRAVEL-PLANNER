// Wait for the DOM to be fully loaded
document.addEventListener("DOMContentLoaded", function () {
  initializeItineraryMap();

  // Add loading state to travel plan form submission
  const planForm = document.querySelector('form[action="/generate_plan"]');
  if (planForm) {
    planForm.addEventListener("submit", function (e) {
      const submitButton = this.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Generating Plan...';
        submitButton.disabled = true;
      }
    });
  }

  // Add loading state to hotel search form submission
  const hotelForm = document.querySelector('form[action="/hotel-search"]');
  if (hotelForm) {
    hotelForm.addEventListener("submit", function (e) {
      const submitButton = this.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.innerHTML =
          '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Searching Hotels...';
        submitButton.disabled = true;
      }
    });
  }

  // Enable Bootstrap tooltips
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]'),
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

function initializeItineraryMap() {
  const map = document.getElementById("itinerary-map");
  const planContent = document.getElementById("plan-content");
  const tabs = document.getElementById("itinerary-day-tabs");
  if (!map || !planContent || !tabs) return;

  const dataElement = document.getElementById("itinerary-map-data");
  let mapDays = [];
  try {
    mapDays = dataElement ? JSON.parse(dataElement.textContent) : [];
  } catch (error) {
    mapDays = [];
  }

  const sections = [...planContent.querySelectorAll("h3")]
    .filter((heading) => /^day\s*\d+/i.test(heading.textContent.trim()))
    .map((heading) => {
      const match = heading.textContent.match(/day\s*(\d+)/i);
      const nodes = [heading];
      let next = heading.nextElementSibling;
      while (
        next &&
        !(next.tagName === "H3" && /^day\s*\d+/i.test(next.textContent.trim()))
      ) {
        nodes.push(next);
        next = next.nextElementSibling;
      }
      return { day: Number(match[1]), nodes };
    });

  const days = mapDays.length
    ? mapDays
    : sections.map((section) => ({ day: section.day, stops: [] }));
  if (!days.length) {
    tabs.hidden = true;
    return;
  }

  const colors = ["#df765c", "#1f6f68", "#d49a4a", "#765a9c", "#3d7ea6"];
  const getStops = (day) =>
    (days.find((item) => Number(item.day) === day) || {}).stops || [];

  function render(dayIndex) {
    const day = days[dayIndex];
    const dayNumber = Number(day.day);
    const color = colors[dayIndex % colors.length];
    tabs.innerHTML = days
      .map(
        (item, index) => `
            <button class="itinerary-day-tab${index === dayIndex ? " active" : ""}" type="button" aria-selected="${index === dayIndex}" data-day-index="${index}">
                <span>Day</span><strong>${item.day}</strong>
            </button>`,
      )
      .join("");
    tabs
      .querySelectorAll("button")
      .forEach((button) =>
        button.addEventListener("click", () =>
          render(Number(button.dataset.dayIndex)),
        ),
      );

    sections.forEach((section) =>
      section.nodes.forEach((node) => {
        node.hidden = section.day !== dayNumber;
      }),
    );
    const stops = getStops(dayNumber);
    const usableStops = stops.filter(
      (stop) =>
        Number.isFinite(Number(stop.lat)) && Number.isFinite(Number(stop.lng)),
    );
    const bounds = usableStops.reduce(
      (result, stop) => ({
        minLat: Math.min(result.minLat, Number(stop.lat)),
        maxLat: Math.max(result.maxLat, Number(stop.lat)),
        minLng: Math.min(result.minLng, Number(stop.lng)),
        maxLng: Math.max(result.maxLng, Number(stop.lng)),
      }),
      {
        minLat: Infinity,
        maxLat: -Infinity,
        minLng: Infinity,
        maxLng: -Infinity,
      },
    );
    const latSpan = Math.max(bounds.maxLat - bounds.minLat, 0.01);
    const lngSpan = Math.max(bounds.maxLng - bounds.minLng, 0.01);
    const position = (stop) => ({
      left: 15 + ((Number(stop.lng) - bounds.minLng) / lngSpan) * 70,
      top: 82 - ((Number(stop.lat) - bounds.minLat) / latSpan) * 64,
    });

    document.getElementById("map-day-count").textContent = `Day ${dayNumber}`;
    document.getElementById("active-day-summary").textContent = stops.length
      ? `${stops.length} places mapped for this day`
      : "The plan for this day is shown below.";
    document.getElementById("journey-stops").innerHTML = usableStops
      .map((stop, index) => {
        const point = position(stop);
        const image =
          stop.image ||
          `https://source.unsplash.com/80x80/?${encodeURIComponent(stop.name || "travel")}`;
        return `<button class="journey-stop" type="button" style="left:${point.left}%;top:${point.top}%;animation-delay:${index * 70}ms" title="${escapeHtml(stop.name || "Place")}">
                <span class="stop-pin" style="background:${color}"><img src="${image}" alt="" loading="lazy"></span><span class="stop-day">${index + 1}</span>
            </button>`;
      })
      .join("");
    document.getElementById("journey-legend").innerHTML = usableStops
      .map(
        (stop, index) =>
          `<div class="journey-legend-item"><span class="legend-dot" style="background:${color}">${index + 1}</span><span><strong>${escapeHtml(stop.name || "Place")}</strong><small>${escapeHtml(stop.time || stop.address || "")}</small></span></div>`,
      )
      .join("");
    document.getElementById("map-route-path").setAttribute(
      "d",
      usableStops.length > 1
        ? usableStops
            .map((stop, index) => {
              const point = position(stop);
              return `${index ? "L" : "M"} ${point.left} ${point.top}`;
            })
            .join(" ")
        : "",
    );
  }

  render(0);
}

function escapeHtml(value) {
  return String(value).replace(
    /[&<>'"]/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        character
      ],
  );
}
