document.querySelectorAll(".toggle-password").forEach(icon => {
  icon.addEventListener("click", () => {
    const targetId = icon.getAttribute("data-target");
    const input = document.getElementById(targetId);

    if (input.type === "password") {
      input.type = "text";
      icon.classList.remove("fa-eye");
      icon.classList.add("fa-eye-slash");
    } else {
      input.type = "password";
      icon.classList.remove("fa-eye-slash");
      icon.classList.add("fa-eye");
    }
  });
});

function validateRegister() {
  const pass = document.getElementById("reg-password").value;
  const confirm = document.getElementById("confirm-password").value;

  if (pass !== confirm) {
    alert("Password dan Konfirmasi Password tidak sama!");
    return false;
  }
  return true;
}

function validateResetPassword() {
  const pass = document.getElementById("new-password").value;
  const confirm = document.getElementById("confirm-password").value;

  if (pass !== confirm) {
    alert("Password dan Konfirmasi Password tidak sama!");
    return false;
  }
  return true;
}

function startOTPTimer() {
  let timeLeft = 60;
  const countdownElement = document.getElementById('countdown');
  const resendBtn = document.getElementById('resend-btn');
  
  if (!countdownElement || !resendBtn) return;

  const countdown = setInterval(() => {
    timeLeft--;
    countdownElement.textContent = timeLeft;
    
    if (timeLeft <= 0) {
      clearInterval(countdown);
      countdownElement.style.display = 'none';
      resendBtn.style.display = 'inline';
    }
  }, 1000);
}

function resendOTP() {
  fetch('/resend-otp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      alert('OTP berhasil dikirim ulang!');
      const countdownElement = document.getElementById('countdown');
      const resendBtn = document.getElementById('resend-btn');
      
      countdownElement.textContent = '60';
      countdownElement.style.display = 'inline';
      resendBtn.style.display = 'none';
      
      startOTPTimer();
    } else {
      alert('Gagal mengirim ulang OTP. Silakan coba lagi.');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Terjadi kesalahan. Silakan coba lagi.');
  });
}

function previewImage(input) {
  const preview = document.getElementById('profile-preview');
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = function(e) {
      preview.src = e.target.result;
    }
    reader.readAsDataURL(input.files[0]);
  }
}

// Like functionality
function toggleLike(postId, button) {
    fetch(`/like/${postId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const likeCountElement = document.getElementById(`like-count-${postId}`);
            const likeIcon = button.querySelector('i');
            
            if (data.action === 'liked') {
                likeIcon.classList.remove('far');
                likeIcon.classList.add('fas');
                likeIcon.style.color = '#ef4444'; // Red color for liked
                button.classList.add('liked');
            } else {
                likeIcon.classList.remove('fas');
                likeIcon.classList.add('far');
                likeIcon.style.color = '';
                button.classList.remove('liked');
            }
            
            if (likeCountElement) {
                likeCountElement.textContent = data.like_count;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Comment modal functionality
function openComments(postId) {
    // Fetch comments first
    fetch(`/comments/${postId}`)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showCommentModal(postId, data.comments);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function showCommentModal(postId, comments) {
    // Create modal overlay
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.7);
        display: flex;
        justify-content: center;
        align-items: flex-end;
        z-index: 10000;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;
    
    // Create modal content
    const modal = document.createElement('div');
    modal.className = 'comment-modal';
    modal.style.cssText = `
        background: var(--bg-card);
        border-radius: 20px 20px 0 0;
        width: 100%;
        max-width: 100%;
        height: 85vh;
        max-height: 85vh;
        display: flex;
        flex-direction: column;
        transform: translateY(100%);
        transition: transform 0.3s ease;
    `;
    
    // Modal header
    const header = document.createElement('div');
    header.style.cssText = `
        padding: 16px;
        border-bottom: 1px solid var(--color-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
    `;
    
    const title = document.createElement('h3');
    title.textContent = 'Komentar';
    title.style.margin = '0';
    
    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '<i class="fas fa-times"></i>';
    closeBtn.style.cssText = `
        background: none;
        border: none;
        color: var(--color-text);
        font-size: 1.2rem;
        cursor: pointer;
    `;
    closeBtn.onclick = closeModal;
    
    header.appendChild(title);
    header.appendChild(closeBtn);
    
    // Comments container
    const commentsContainer = document.createElement('div');
    commentsContainer.className = 'comments-container';
    commentsContainer.style.cssText = `
        flex: 1;
        overflow-y: auto;
        padding: 16px;
    `;
    
    // Add comments to container
    if (comments.length > 0) {
        comments.forEach(comment => {
            // Check if current user is the comment author
            const isCurrentUser = comment.user_id === parseInt('{{ session.user_id }}');
            const commentElement = createCommentElement(comment, postId, isCurrentUser);
            commentsContainer.appendChild(commentElement);
        });
    } else {
        const emptyMessage = document.createElement('p');
        emptyMessage.textContent = 'Belum ada komentar. Jadilah yang pertama berkomentar!';
        emptyMessage.style.cssText = `
            text-align: center;
            color: var(--color-text-secondary);
            margin: 20px 0;
        `;
        commentsContainer.appendChild(emptyMessage);
    }
    
    // Comment input area
    const inputContainer = document.createElement('div');
    inputContainer.style.cssText = `
        padding: 16px;
        border-top: 1px solid var(--color-border);
        display: flex;
        gap: 10px;
    `;
    
    const commentInput = document.createElement('input');
    commentInput.type = 'text';
    commentInput.placeholder = 'Tambah komentar...';
    commentInput.style.cssText = `
        flex: 1;
        padding: 12px 16px;
        background: rgba(21, 21, 21, 0.8);
        border: 1px solid var(--color-border);
        border-radius: 20px;
        color: var(--color-text);
        font-size: 14px;
    `;
    
    const sendButton = document.createElement('button');
    sendButton.innerHTML = '<i class="fas fa-arrow-up"></i>';
    sendButton.style.cssText = `
        background: var(--color-primary);
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    `;
    sendButton.onclick = () => postComment(postId, commentInput);
    
    commentInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            postComment(postId, commentInput);
        }
    });
    
    inputContainer.appendChild(commentInput);
    inputContainer.appendChild(sendButton);
    
    // Assemble modal
    modal.appendChild(header);
    modal.appendChild(commentsContainer);
    modal.appendChild(inputContainer);
    overlay.appendChild(modal);
    
    // Add to document
    document.body.appendChild(overlay);
    
    // Animate in
    setTimeout(() => {
        overlay.style.opacity = '1';
        modal.style.transform = 'translateY(0)';
    }, 10);
    
    // Focus input
    setTimeout(() => {
        commentInput.focus();
    }, 300);
    
    function closeModal() {
        overlay.style.opacity = '0';
        modal.style.transform = 'translateY(100%)';
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 300);
    }
    
    overlay.onclick = (e) => {
        if (e.target === overlay) {
            closeModal();
        }
    };
}

// Update the createCommentElement function to include verified badge
function createCommentElement(comment, postId, isCurrentUser = false) {
    const commentDiv = document.createElement('div');
    commentDiv.id = `comment-${comment.id}`;
    commentDiv.style.cssText = `
        display: flex;
        gap: 12px;
        margin-bottom: 16px;
        position: relative;
    `;
    
    const avatar = document.createElement('div');
    if (comment.profile_picture) {
        const img = document.createElement('img');
        img.src = `/static/uploads/${comment.profile_picture}`;
        img.alt = comment.username;
        img.style.cssText = `
            width: 36px;
            height: 36px;
            border-radius: 50%;
            object-fit: cover;
        `;
        avatar.appendChild(img);
    } else {
        const placeholder = document.createElement('div');
        placeholder.style.cssText = `
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: var(--color-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        `;
        placeholder.textContent = comment.username.charAt(0).toUpperCase();
        avatar.appendChild(placeholder);
    }
    
    const content = document.createElement('div');
    content.style.cssText = `
        flex: 1;
    `;
    
    const usernameContainer = document.createElement('div');
    usernameContainer.style.cssText = `
        display: flex;
        align-items: center;
        gap: 4px;
        margin-bottom: 4px;
    `;
    
    const username = document.createElement('span');
    username.style.cssText = `
        font-weight: 600;
        color: var(--color-text);
    `;
    username.textContent = comment.display_name || comment.username;
    
    usernameContainer.appendChild(username);
    
    // Tambahkan verified badge jika user terverifikasi
    if (comment.is_verified) {
        const verifiedBadge = document.createElement('span');
        verifiedBadge.className = 'verified-badge';
        verifiedBadge.title = 'Akun Terverifikasi';
        verifiedBadge.style.cssText = `
            display: inline-flex;
            align-items: center;
            color: #3897f0;
            font-size: 12px;
        `;
        
        const icon = document.createElement('i');
        icon.className = 'fas fa-check-circle';
        icon.style.cssText = `
            font-size: 12px;
        `;
        
        verifiedBadge.appendChild(icon);
        usernameContainer.appendChild(verifiedBadge);
    }
    
    const commentText = document.createElement('div');
    commentText.style.cssText = `
        color: var(--color-text);
        margin-bottom: 4px;
        line-height: 1.4;
        font-size: 14px;
    `;
    commentText.textContent = comment.content;
    
    const time = document.createElement('div');
    time.style.cssText = `
        font-size: 12px;
        color: var(--color-text-secondary);
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    time.textContent = comment.created_at;
    
    // Add delete button if current user is the comment author
    if (isCurrentUser) {
        const deleteBtn = document.createElement('button');
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.style.cssText = `
            background: none;
            border: none;
            color: var(--color-text-secondary);
            cursor: pointer;
            padding: 4px;
            font-size: 12px;
            margin-left: 8px;
        `;
        deleteBtn.onclick = () => deleteComment(comment.id, postId);
        deleteBtn.title = 'Hapus komentar';
        time.appendChild(deleteBtn);
    }
    
    content.appendChild(usernameContainer);
    content.appendChild(commentText);
    content.appendChild(time);
    
    commentDiv.appendChild(avatar);
    commentDiv.appendChild(content);
    
    return commentDiv;
}

function postComment(postId, inputElement) {
    const content = inputElement.value.trim();
    if (!content) return;
    
    fetch(`/comment/${postId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content: content })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Clear input
            inputElement.value = '';
            
            // Add new comment to the list
            const commentsContainer = document.querySelector('.comments-container');
            
            // Remove empty message if exists
            const emptyMessage = commentsContainer.querySelector('p');
            if (emptyMessage) {
                commentsContainer.removeChild(emptyMessage);
            }
            
            // Add new comment
            const commentElement = createCommentElement(data.comment);
            commentsContainer.insertBefore(commentElement, commentsContainer.firstChild);
            
            // Update comment count on the post
            const commentCountElement = document.getElementById(`comment-count-${postId}`);
            if (commentCountElement) {
                const currentCount = parseInt(commentCountElement.textContent) || 0;
                commentCountElement.textContent = currentCount + 1;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function deleteComment(commentId, postId) {
    if (!confirm('Apakah Anda yakin ingin menghapus komentar ini?')) {
        return;
    }
    
    fetch(`/delete-comment/${commentId}`, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove comment from DOM
            const commentElement = document.getElementById(`comment-${commentId}`);
            if (commentElement) {
                commentElement.remove();
            }
            
            // Update comment count
            const commentCountElement = document.getElementById(`comment-count-${postId}`);
            if (commentCountElement) {
                const currentCount = parseInt(commentCountElement.textContent) || 0;
                commentCountElement.textContent = Math.max(0, currentCount - 1) + ' comments';
            }
            
            // If no comments left, show empty message
            const commentsContainer = document.querySelector('.comments-container');
            if (commentsContainer && commentsContainer.children.length === 0) {
                const emptyMessage = document.createElement('p');
                emptyMessage.textContent = 'Belum ada komentar. Jadilah yang pertama berkomentar!';
                emptyMessage.style.cssText = `
                    text-align: center;
                    color: var(--color-text-secondary);
                    margin: 20px 0;
                `;
                commentsContainer.appendChild(emptyMessage);
            }
        } else {
            alert('Gagal menghapus komentar: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Terjadi kesalahan saat menghapus komentar');
    });
}

// Search History Functions
function clearSearchHistory() {
    if (!confirm('Apakah Anda yakin ingin menghapus semua riwayat pencarian?')) {
        return;
    }
    
    fetch('/clear-search-history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove all search history items from DOM
            const searchHistoryItems = document.querySelectorAll('.search-history-item');
            searchHistoryItems.forEach(item => {
                item.style.transition = 'all 0.3s ease';
                item.style.opacity = '0';
                item.style.transform = 'translateX(-100px)';
                
                setTimeout(() => {
                    if (item.parentNode) {
                        item.parentNode.removeChild(item);
                    }
                }, 300);
            });
            
            // Show empty state or hide history container
            const historyContainer = document.querySelector('.search-history-container');
            if (historyContainer) {
                setTimeout(() => {
                    historyContainer.style.display = 'none';
                }, 300);
            }
            
            showNotification('Riwayat pencarian berhasil dihapus', 'success');
        } else {
            showNotification('Gagal menghapus riwayat pencarian', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat menghapus riwayat', 'error');
    });
}

function removeSearchItem(query, element) {
    fetch('/remove-search-item', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove the item from DOM with animation
            element.style.transition = 'all 0.3s ease';
            element.style.opacity = '0';
            element.style.transform = 'translateX(-100px)';
            
            setTimeout(() => {
                if (element.parentNode) {
                    element.parentNode.removeChild(element);
                }
            }, 300);
            
            showNotification('Item pencarian dihapus', 'success');
        } else {
            showNotification('Gagal menghapus item pencarian', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Terjadi kesalahan saat menghapus item', 'error');
    });
}

function performSearch(query) {
    const searchForm = document.querySelector('.search-form');
    const searchInput = searchForm.querySelector('input[name="q"]');
    
    if (searchForm && searchInput) {
        searchInput.value = query;
        searchForm.submit();
    } else {
        // Fallback: redirect to search page
        window.location.href = `/search?q=${encodeURIComponent(query)}`;
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 14px;
        padding: 8px 18px;
        border-radius: 18px;
        color: white;
        font-weight: 500;
        z-index: 10001;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
        word-wrap: break-word;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    `;
    
    // Set background color based on type
    switch (type) {
        case 'success':
            notification.style.backgroundColor = '#10b981';
            break;
        case 'error':
            notification.style.backgroundColor = '#ef4444';
            break;
        case 'warning':
            notification.style.backgroundColor = '#f59e0b';
            break;
        default:
            notification.style.backgroundColor = '#3b82f6';
    }
    
    notification.textContent = message;
    
    // Add to document
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 10);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded'); // Debug log
    
    startOTPTimer();
    
    const usernameInputs = document.querySelectorAll('input[name="username"], input[name="identity"]');
    
    usernameInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            const cursorPosition = e.target.selectionStart;
            const originalLength = e.target.value.length;
            
            const cleanValue = e.target.value.replace(/\s/g, '');
            
            e.target.value = cleanValue;
            
            const lengthDifference = originalLength - cleanValue.length;
            
            const newCursorPosition = cursorPosition - lengthDifference;
            
            e.target.setSelectionRange(newCursorPosition, newCursorPosition);
        });
        
        input.addEventListener('paste', function(e) {
            setTimeout(function() {
                const cleanValue = e.target.value.replace(/\s/g, '');
                e.target.value = cleanValue;
            }, 10);
        });
        
        input.addEventListener('keydown', function(e) {
            if (e.key === ' ') {
                e.target.style.borderColor = '#3b82f6';
                e.target.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.2)';
                
                setTimeout(function() {
                    e.target.style.borderColor = '';
                    e.target.style.boxShadow = '';
                }, 200);
            }
        });
    });
    
    const fileInput = document.getElementById('profile_picture');
    if (fileInput) {
        fileInput.addEventListener('change', function() {
            previewImage(this);
        });
    }
    
    const postImageInput = document.getElementById('post_image');
    const imagePreview = document.getElementById('image-preview');
    
    if (postImageInput && imagePreview) {
        postImageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    imagePreview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                    imagePreview.style.display = 'block';
                }
                
                reader.readAsDataURL(this.files[0]);
            } else {
                imagePreview.style.display = 'none';
                imagePreview.innerHTML = '';
            }
        });
    }
    
    const profileImageInput = document.getElementById('profile_picture');
    const avatarPreview = document.getElementById('avatar-preview');
    
    if (profileImageInput && avatarPreview) {
        profileImageInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    if (avatarPreview.tagName === 'IMG') {
                        avatarPreview.src = e.target.result;
                    } else {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.alt = "Avatar preview";
                        avatarPreview.parentNode.replaceChild(img, avatarPreview);
                    }
                }
                
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
    
    // === SEARCH HISTORY HANDLERS - FIXED VERSION ===
    
    // Clear all search history
    const clearHistoryBtn = document.querySelector('.clear-history-btn');
    if (clearHistoryBtn) {
        console.log('Clear history button found'); // Debug log
        clearHistoryBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            clearSearchHistory();
        });
    }
    
    // Handle search history items
    const searchHistoryItems = document.querySelectorAll('.search-history-item');
    console.log('Found search history items:', searchHistoryItems.length); // Debug log
    
    searchHistoryItems.forEach(function(item, index) {
        console.log(`Setting up handlers for item ${index}`); // Debug log
        
        // Handle clicking on history item to search (but not on remove button)
        item.addEventListener('click', function(e) {
            console.log('History item clicked', e.target); // Debug log
            
            // Only perform search if the remove button wasn't clicked
            if (!e.target.closest('.remove-history-item')) {
                const querySpan = this.querySelector('.history-query span');
                if (querySpan) {
                    const query = querySpan.textContent.trim();
                    console.log('Performing search for:', query); // Debug log
                    performSearch(query);
                }
            }
        });
        
        // Handle remove button click
        const removeBtn = item.querySelector('.remove-history-item');
        if (removeBtn) {
            console.log(`Remove button found for item ${index}`); // Debug log
            
            removeBtn.addEventListener('click', function(e) {
                console.log('Remove button clicked'); // Debug log
                
                e.preventDefault();
                e.stopPropagation(); // Prevent parent click handler
                
                // Get query from data attribute
                const query = this.getAttribute('data-query');
                console.log('Removing query:', query); // Debug log
                
                if (query) {
                    removeSearchItem(query, item);
                } else {
                    console.error('No query found in data-query attribute');
                }
            });
        } else {
            console.log(`No remove button found for item ${index}`); // Debug log
        }
    });
    
    // Focus search input if no query parameter
    const searchInput = document.querySelector('input[name="q"]');
    if (searchInput) {
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.get('q')) {
            setTimeout(() => {
                searchInput.focus();
            }, 100);
        }
    }
});