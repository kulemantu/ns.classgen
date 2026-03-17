// ClassGen Service Worker -- handles push notifications

self.addEventListener('push', function(event) {
  let data = {title: 'ClassGen', body: 'New notification', url: '/'};
  try {
    data = event.data.json();
  } catch (e) {
    data.body = event.data ? event.data.text() : 'New notification';
  }

  const options = {
    body: data.body,
    icon: '/static/icon-192.png',
    badge: '/static/icon-192.png',
    tag: data.tag || 'classgen',
    data: {url: data.url || '/'},
    vibrate: [200, 100, 200],
    actions: [
      {action: 'open', title: 'View'},
    ],
  };

  event.waitUntil(
    self.registration.showNotification(data.title, options)
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(
    clients.matchAll({type: 'window', includeUncontrolled: true}).then(function(clientList) {
      // Focus existing tab if open
      for (const client of clientList) {
        if (client.url.includes(url) && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new tab
      return clients.openWindow(url);
    })
  );
});
