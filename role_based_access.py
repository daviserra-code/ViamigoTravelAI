"""
Role-based access control and user management for ViamigoTravelAI
Enhanced admin system with mobile-responsive interface
"""

from functools import wraps
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash
import logging
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
role_based_access_bp = Blueprint('role_based_access', __name__)


class UserRoleManager:
    """Manages user roles and permissions"""

    def __init__(self):
        self.roles = {
            'admin': {
                'name': 'Administrator',
                'permissions': [
                    'view_analytics', 'manage_users', 'system_config',
                    'performance_monitor', 'data_management', 'all_features'
                ],
                'description': 'Full system access'
            },
            'pro': {
                'name': 'Pro User',
                'permissions': [
                    'budget_optimizer', 'travel_insights', 'advanced_planning',
                    'custom_reports', 'premium_features'
                ],
                'description': 'Premium travel features'
            },
            'basic': {
                'name': 'Basic User',
                'permissions': ['basic_search', 'route_planning', 'basic_features'],
                'description': 'Standard travel planning'
            }
        }

        # Default admin user (in production, this would be in database)
        self.users = {
            'admin@viamigo.ai': {
                'role': 'admin',
                'name': 'System Administrator',
                'created': datetime.now(),
                'last_login': datetime.now(),
                'active': True
            }
        }

    def get_user_role(self, user_email=None):
        """Get user role from session or email"""
        if user_email:
            return self.users.get(user_email, {}).get('role', 'basic')

        # Check session for demo purposes
        return session.get('user_role', 'admin')  # Default admin for demo

    def has_permission(self, user_email, permission):
        """Check if user has specific permission"""
        role = self.get_user_role(user_email)
        if role not in self.roles:
            return False

        return permission in self.roles[role]['permissions']

    def require_permission(self, permission):
        """Decorator to require specific permission"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_email = session.get('user_email', 'admin@viamigo.ai')

                if not self.has_permission(user_email, permission):
                    if request.is_json:
                        return jsonify({
                            'error': 'Insufficient permissions',
                            'required_permission': permission
                        }), 403
                    else:
                        flash(
                            f'Access denied. Required permission: {permission}', 'error')
                        return redirect(url_for('role_based_access.access_denied'))

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def require_role(self, required_role):
        """Decorator to require specific role"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_email = session.get('user_email', 'admin@viamigo.ai')
                user_role = self.get_user_role(user_email)

                if user_role != required_role and required_role != 'admin':
                    if request.is_json:
                        return jsonify({
                            'error': 'Insufficient role',
                            'required_role': required_role,
                            'current_role': user_role
                        }), 403
                    else:
                        flash(
                            f'Access denied. Required role: {required_role}', 'error')
                        return redirect(url_for('role_based_access.access_denied'))

                return f(*args, **kwargs)
            return decorated_function
        return decorator


# Initialize role manager
role_manager = UserRoleManager()


@role_based_access_bp.route('/mobile_admin')
def mobile_admin_dashboard():
    """Mobile-responsive admin dashboard"""
    try:
        # Check if user has any admin or pro permissions
        user_email = session.get('user_email', 'admin@viamigo.ai')
        user_role = role_manager.get_user_role(user_email)

        if user_role == 'basic':
            flash('Upgrade to Pro or Admin for dashboard access', 'info')
            return redirect(url_for('main.index'))

        logger.info(f"✅ Mobile admin dashboard accessed by role: {user_role}")

        # Serve the new mobile-styled admin dashboard that matches main app design
        return open('/workspaces/ViamigoTravelAI/static/mobile_admin_v2.html', 'r').read()

    except Exception as e:
        logger.error(f"❌ Mobile admin dashboard error: {e}")
        return jsonify({'error': 'Dashboard unavailable'}), 500


@role_based_access_bp.route('/api/admin/stats')
@role_manager.require_permission('view_analytics')
def admin_stats():
    """Get admin statistics for dashboard"""
    try:
        # In a real implementation, these would come from database queries
        stats = {
            'totalPlaces': 9930,
            'activeUsers': 156,
            'uptime': 98.7,
            'responseTime': 245,
            'systemHealth': 'excellent',
            'lastUpdate': datetime.now().isoformat()
        }

        logger.info("✅ Admin stats retrieved successfully")
        return jsonify(stats)

    except Exception as e:
        logger.error(f"❌ Admin stats error: {e}")
        return jsonify({'error': 'Stats unavailable'}), 500


@role_based_access_bp.route('/admin/config')
@role_manager.require_role('admin')
def system_config():
    """System configuration interface (admin only)"""
    return jsonify({
        'message': 'System Configuration Interface',
        'features': [
            'Database Settings',
            'API Configuration',
            'Security Settings',
            'Performance Tuning',
            'Backup Management'
        ],
        'access_level': 'admin_only'
    })


@role_based_access_bp.route('/admin/users')
@role_manager.require_role('admin')
def user_management():
    """User management interface (admin only)"""
    return jsonify({
        'message': 'User Management Interface',
        'features': [
            'Role Assignment',
            'Permission Management',
            'User Activity Logs',
            'Subscription Management',
            'Access Control'
        ],
        'access_level': 'admin_only'
    })


@role_based_access_bp.route('/admin/data')
@role_manager.require_role('admin')
def data_management():
    """Data management tools (admin only)"""
    return jsonify({
        'message': 'Data Management Tools',
        'features': [
            'Database Operations',
            'Data Import/Export',
            'Backup & Restore',
            'Data Integrity Checks',
            'Performance Optimization'
        ],
        'access_level': 'admin_only'
    })


@role_based_access_bp.route('/budget_optimizer')
@role_manager.require_permission('budget_optimizer')
def budget_optimizer():
    """Budget optimization tools (pro users)"""
    return jsonify({
        'message': 'Budget Optimizer',
        'features': [
            'Smart Budget Planning',
            'Cost Analysis',
            'Expense Tracking',
            'Savings Recommendations',
            'Currency Optimization'
        ],
        'access_level': 'pro_users'
    })


@role_based_access_bp.route('/travel_insights')
@role_manager.require_permission('travel_insights')
def travel_insights():
    """Travel insights and recommendations (pro users)"""
    return jsonify({
        'message': 'Travel Insights',
        'features': [
            'Personalized Recommendations',
            'Seasonal Analysis',
            'Crowd Predictions',
            'Weather Integration',
            'Local Tips & Secrets'
        ],
        'access_level': 'pro_users'
    })


@role_based_access_bp.route('/advanced_planning')
@role_manager.require_permission('advanced_planning')
def advanced_planning():
    """Advanced trip planning (pro users)"""
    return jsonify({
        'message': 'Advanced Trip Planning',
        'features': [
            'Multi-day Itineraries',
            'Real-time Optimization',
            'Group Travel Coordination',
            'Activity Suggestions',
            'Transportation Integration'
        ],
        'access_level': 'pro_users'
    })


@role_based_access_bp.route('/custom_reports')
@role_manager.require_permission('custom_reports')
def custom_reports():
    """Custom reporting tools (pro users)"""
    return jsonify({
        'message': 'Custom Reports',
        'features': [
            'Travel Statistics',
            'Expense Reports',
            'Performance Analytics',
            'Export Options',
            'Scheduled Reports'
        ],
        'access_level': 'pro_users'
    })


@role_based_access_bp.route('/api/user/role')
def get_user_role():
    """Get current user role for frontend"""
    try:
        user_email = session.get('user_email', 'admin@viamigo.ai')
        user_role = role_manager.get_user_role(user_email)

        return jsonify({
            'role': user_role,
            'permissions': role_manager.roles.get(user_role, {}).get('permissions', []),
            'description': role_manager.roles.get(user_role, {}).get('description', 'Unknown')
        })

    except Exception as e:
        logger.error(f"❌ Get user role error: {e}")
        return jsonify({'error': 'Role check failed'}), 500


@role_based_access_bp.route('/access_denied')
def access_denied():
    """Access denied page"""
    return jsonify({
        'error': 'Access Denied',
        'message': 'You do not have permission to access this resource',
        'upgrade_info': 'Consider upgrading to Pro or Admin for additional features'
    }), 403


@role_based_access_bp.route('/api/features/check')
def check_feature_access():
    """Check access to specific features"""
    try:
        feature = request.args.get('feature')
        user_email = session.get('user_email', 'admin@viamigo.ai')

        if not feature:
            return jsonify({'error': 'Feature parameter required'}), 400

        has_access = role_manager.has_permission(user_email, feature)
        user_role = role_manager.get_user_role(user_email)

        return jsonify({
            'feature': feature,
            'access': has_access,
            'user_role': user_role,
            'message': 'Access granted' if has_access else 'Access denied'
        })

    except Exception as e:
        logger.error(f"❌ Feature access check error: {e}")
        return jsonify({'error': 'Feature check failed'}), 500


# Export the role manager for use in other modules
__all__ = ['role_based_access_bp', 'role_manager']
