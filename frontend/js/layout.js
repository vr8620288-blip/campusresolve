/**
 * Renders the sidebar + topbar shell used on every authenticated page,
 * and wires up the notification bell.
 */
const NAV_ITEMS = {
  STUDENT: [
    { href: "dashboard.html", label: "Dashboard", icon: "🏠" },
    { href: "complaints.html", label: "My Complaints", icon: "📋" },
    { href: "complaints.html?new=1", label: "Submit Complaint", icon: "➕" },
    { href: "profile.html", label: "Profile", icon: "👤" },
  ],
  STAFF: [
    { href: "dashboard.html", label: "Dashboard", icon: "🏠" },
    { href: "staff.html", label: "Assigned Complaints", icon: "📋" },
    { href: "profile.html", label: "Profile", icon: "👤" },
  ],
  ADMIN: [
    { href: "dashboard.html", label: "Dashboard", icon: "🏠" },
    { href: "admin.html", label: "All Complaints", icon: "📋" },
    { href: "admin.html?tab=users", label: "Users & Staff", icon: "👥" },
    { href: "admin.html?tab=catalog", label: "Categories & Depts.", icon: "🗂️" },
    { href: "profile.html", label: "Profile", icon: "👤" },
  ],
};

function renderShell({ title, activeHref }) {
  const role = Session.role();
  const items = NAV_ITEMS[role] || [];
  const navHtml = items
    .map((item) => {
      const isActive = activeHref && item.href.startsWith(activeHref);
      return `<a href="${item.href}" class="${isActive ? "active" : ""}"><span>${item.icon}</span> ${item.label}</a>`;
    })
    .join("");

  const shell = document.createElement("div");
  shell.className = "app-shell";
  shell.innerHTML = `
    <aside class="sidebar">
      <div class="brand"><span class="dot"></span> CampusResolve</div>
      <nav>${navHtml}</nav>
      <div class="sidebar-footer">${Session.name() || ""}<br/>${role}</div>
    </aside>
    <div class="main-area">
      <header class="topbar">
        <h1>${title}</h1>
        <div class="topbar-right">
          <button class="icon-btn" id="notif-btn" title="Notifications">🔔<span id="notif-dot" class="notif-dot" style="display:none">0</span></button>
          <button class="btn btn-outline btn-sm" id="logout-btn">Logout</button>
        </div>
      </header>
      <main class="content" id="page-content"></main>
    </div>
    <div id="notif-panel" class="card" style="display:none; position:absolute; right:20px; top:60px; width:340px; max-height:420px; overflow-y:auto; z-index:200;"></div>
  `;
  document.body.prepend(shell);

  document.getElementById("logout-btn").addEventListener("click", () => Session.logout());
  document.getElementById("notif-btn").addEventListener("click", toggleNotifPanel);

  refreshNotifBadge();
  setInterval(refreshNotifBadge, 30000);

  return document.getElementById("page-content");
}

async function refreshNotifBadge() {
  try {
    const data = await Api.listNotifications();
    const dot = document.getElementById("notif-dot");
    if (!dot) return;
    if (data.unread_count > 0) {
      dot.style.display = "inline-block";
      dot.textContent = data.unread_count > 9 ? "9+" : data.unread_count;
    } else {
      dot.style.display = "none";
    }
  } catch (e) {
    // silent fail on badge refresh
  }
}

async function toggleNotifPanel() {
  const panel = document.getElementById("notif-panel");
  if (panel.style.display === "block") {
    panel.style.display = "none";
    return;
  }
  panel.style.display = "block";
  panel.innerHTML = '<div class="loading-state"><div class="spinner"></div>Loading…</div>';
  try {
    const data = await Api.listNotifications();
    if (!data.items.length) {
      panel.innerHTML = '<div class="empty-state">No notifications yet.</div>';
      return;
    }
    panel.innerHTML = data.items
      .map(
        (n) => `
        <div class="notif-item ${n.is_read ? "" : "unread"}" data-id="${n.id}" data-complaint="${n.complaint_id || ""}">
          <div class="n-title">${escapeHtml(n.title)}</div>
          <div>${escapeHtml(n.message)}</div>
          <div class="n-meta">${formatDate(n.created_at)}</div>
        </div>`
      )
      .join("");
    panel.querySelectorAll(".notif-item").forEach((el) => {
      el.addEventListener("click", async () => {
        const id = el.getAttribute("data-id");
        const complaintId = el.getAttribute("data-complaint");
        await Api.markNotificationRead(id).catch(() => {});
        refreshNotifBadge();
        if (complaintId) {
          window.location.href = `complaint-details.html?id=${complaintId}`;
        }
      });
    });
  } catch (e) {
    panel.innerHTML = `<div class="error-state">${escapeHtml(e.message)}</div>`;
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}
