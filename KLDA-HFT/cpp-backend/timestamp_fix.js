                // Get latest tick time
                const latestBar = bars[bars.length - 1];
                if (latestBar) {
                    const lastTime = new Date(latestBar.time);
                    const secondsAgo = Math.floor((Date.now() - lastTime.getTime()) / 1000);
                    const minutesAgo = Math.floor(secondsAgo / 60);
                    const hoursAgo = Math.floor(secondsAgo / 3600);
                    const daysAgo = Math.floor(secondsAgo / 86400);

                    let timeAgo;
                    if (secondsAgo < 60) timeAgo = `${secondsAgo}s ago`;
                    else if (minutesAgo < 60) timeAgo = `${minutesAgo}m ago`;
                    else if (hoursAgo < 24) timeAgo = `${hoursAgo}h ago`;
                    else timeAgo = `${daysAgo}d ago`;

                    // Show absolute timestamp AND relative time
                    const absoluteTime = lastTime.toLocaleString();

                    // Color code based on data staleness
                    let color = '#0f0'; // green = live (< 60s)
                    let warning = '';
                    if (secondsAgo > 600) { // > 10 minutes
                        color = '#f00'; // red = stale
                        if (daysAgo >= 1) {
                            warning = ` [MARKET CLOSED - Last: ${daysAgo}d ago]`;
                        } else {
                            warning = ' [STALE DATA]';
                        }
                    } else if (secondsAgo > 60) { // > 1 minute
                        color = '#ff0'; // yellow = delayed
                    }

                    document.getElementById('stat-updated').innerHTML =
                        `<span style="color: ${color}; font-size: 12px;">${absoluteTime}<br>${timeAgo}${warning}</span>`;
                } else {
                    document.getElementById('stat-updated').innerHTML =
                        '<span style="color: #f00;">Unknown</span>';
                }
