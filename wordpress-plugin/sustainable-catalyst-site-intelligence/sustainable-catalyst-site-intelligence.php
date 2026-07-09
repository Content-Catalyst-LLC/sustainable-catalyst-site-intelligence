<?php
/**
 * Plugin Name: Sustainable Catalyst Site Intelligence
 * Description: Connects Sustainable Catalyst pages to the Site Intelligence backend, GA4/dataLayer custom events, and shortcode dashboards.
 * Version: 0.6.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

final class SC_Site_Intelligence_Plugin {
    const OPTION_KEY = 'sc_site_intelligence_options';
    const VERSION = '0.6.0';
    const REST_NAMESPACE = 'sc-site-intelligence/v1';

    public function __construct() {
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        add_action('rest_api_init', [$this, 'register_rest_routes']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_assets']);
        add_shortcode('sc_site_intelligence_dashboard', [$this, 'dashboard_shortcode']);
        add_shortcode('sc_site_intelligence_page', [$this, 'page_shortcode']);
        add_shortcode('sc_site_intelligence_unmapped', [$this, 'unmapped_shortcode']);
        add_shortcode('sc_site_intelligence_events', [$this, 'events_shortcode']);
        add_shortcode('sc_site_intelligence_opportunities', [$this, 'opportunities_shortcode']);
        add_shortcode('sc_external_data_health', [$this, 'external_health_shortcode']);
        add_shortcode('sc_climate_energy_intelligence', [$this, 'climate_energy_shortcode']);
        add_shortcode('sc_external_cache_status', [$this, 'external_cache_shortcode']);
        add_shortcode('sc_search_intelligence', [$this, 'search_intelligence_shortcode']);
        add_shortcode('sc_search_opportunities', [$this, 'search_opportunities_shortcode']);
        add_shortcode('sc_metadata_intelligence', [$this, 'metadata_intelligence_shortcode']);
        add_shortcode('sc_internal_link_intelligence', [$this, 'internal_link_intelligence_shortcode']);
        add_shortcode('sc_seo_recommendations', [$this, 'seo_recommendations_shortcode']);
        add_shortcode('sc_indexing_intelligence', [$this, 'indexing_intelligence_shortcode']);
        add_shortcode('sc_sitemap_coverage', [$this, 'sitemap_coverage_shortcode']);
        add_shortcode('sc_404_intelligence', [$this, 'four_oh_four_intelligence_shortcode']);
        add_shortcode('sc_content_strategy_intelligence', [$this, 'content_strategy_shortcode']);
        add_shortcode('sc_topic_momentum', [$this, 'topic_momentum_shortcode']);
        add_shortcode('sc_update_priorities', [$this, 'update_priorities_shortcode']);
        add_shortcode('sc_publishing_opportunities', [$this, 'publishing_opportunities_shortcode']);
        add_shortcode('sc_site_intelligence_public_landing', [$this, 'public_landing_shortcode']);
        add_shortcode('sc_public_site_intelligence', [$this, 'public_site_intelligence_shortcode']);
        add_shortcode('sc_public_knowledge_overview', [$this, 'public_knowledge_overview_shortcode']);
        add_shortcode('sc_public_climate_energy_summary', [$this, 'public_climate_energy_summary_shortcode']);
        add_shortcode('sc_public_methodology', [$this, 'public_methodology_shortcode']);
        add_shortcode('sc_public_dashboard_readiness', [$this, 'public_dashboard_readiness_shortcode']);
        add_shortcode('sc_advanced_external_data_health', [$this, 'advanced_external_health_shortcode']);
        add_shortcode('sc_environmental_monitoring_intelligence', [$this, 'environmental_monitoring_shortcode']);
        add_shortcode('sc_urban_resilience_intelligence', [$this, 'urban_resilience_shortcode']);
        add_shortcode('sc_biodiversity_land_use_intelligence', [$this, 'biodiversity_land_use_shortcode']);
        add_shortcode('sc_energy_systems_intelligence', [$this, 'energy_systems_shortcode']);
    }

    public static function defaults() {
        return [
            'backend_url' => '',
            'api_token' => '',
            'enable_event_bridge' => '1',
            'enable_dashboard' => '1',
        ];
    }

    public static function options() {
        return wp_parse_args(get_option(self::OPTION_KEY, []), self::defaults());
    }

    public function admin_menu() {
        add_options_page(
            'SC Site Intelligence',
            'SC Site Intelligence',
            'manage_options',
            'sc-site-intelligence',
            [$this, 'settings_page']
        );
    }

    public function register_settings() {
        register_setting('sc_site_intelligence', self::OPTION_KEY, [
            'type' => 'array',
            'sanitize_callback' => [$this, 'sanitize_options'],
        ]);
    }

    public function sanitize_options($input) {
        $defaults = self::defaults();
        $output = [];
        $output['backend_url'] = isset($input['backend_url']) ? esc_url_raw(trim($input['backend_url'])) : $defaults['backend_url'];
        $output['api_token'] = isset($input['api_token']) ? sanitize_text_field($input['api_token']) : $defaults['api_token'];
        $output['enable_event_bridge'] = !empty($input['enable_event_bridge']) ? '1' : '0';
        $output['enable_dashboard'] = !empty($input['enable_dashboard']) ? '1' : '0';
        return $output;
    }

    public function register_rest_routes() {
        register_rest_route(self::REST_NAMESPACE, '/dashboard', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_dashboard'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/page', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_page'],
            'permission_callback' => '__return_true',
            'args' => [
                'path' => [
                    'required' => true,
                    'sanitize_callback' => 'sanitize_text_field',
                ],
            ],
        ]);
        register_rest_route(self::REST_NAMESPACE, '/unmapped', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_unmapped'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/events', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_events'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/opportunities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_opportunities'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/conversions', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_conversions'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/external-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_external_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/external-cache', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_external_cache'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/climate-energy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_climate_energy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/search-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_search_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/search-opportunities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_search_opportunities'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/search-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_search_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/metadata-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_metadata_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/internal-link-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_internal_link_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/seo-recommendations', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_seo_recommendations'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/indexing-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_indexing_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/sitemap-coverage', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_sitemap_coverage'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/404-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_404_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/indexing-recommendations', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_indexing_recommendations'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/content-strategy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_content_strategy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/topic-momentum', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_topic_momentum'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/update-priorities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_update_priorities'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/publishing-opportunities', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_publishing_opportunities'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-landing-page', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_landing_page'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-knowledge-overview', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_knowledge_overview'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-climate-energy-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_climate_energy_summary'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-methodology', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_methodology'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-readiness', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_readiness'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);

        register_rest_route(self::REST_NAMESPACE, '/advanced-external-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_advanced_external_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/environmental-monitoring', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_environmental_monitoring'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/urban-resilience', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_urban_resilience'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/biodiversity-land-use', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_biodiversity_land_use'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/energy-systems', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_energy_systems'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/event', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [$this, 'rest_event'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/diagnostics/ga4', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ga4_diagnostics'],
            'permission_callback' => '__return_true',
        ]);
    }

    private function backend_request($endpoint, $method = 'GET', $body = null) {
        $options = self::options();
        if (empty($options['backend_url'])) {
            return new WP_Error('scsi_no_backend', 'Site Intelligence backend URL is not configured.', ['status' => 400]);
        }
        $url = untrailingslashit($options['backend_url']) . '/' . ltrim($endpoint, '/');
        $args = [
            'method' => $method,
            'timeout' => 12,
            'headers' => [
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
            ],
        ];
        if (!empty($options['api_token'])) {
            $args['headers']['X-SC-Intelligence-Token'] = $options['api_token'];
        }
        if (!is_null($body)) {
            $args['body'] = wp_json_encode($body);
        }
        $response = wp_remote_request($url, $args);
        if (is_wp_error($response)) {
            return $response;
        }
        $code = wp_remote_retrieve_response_code($response);
        $raw_body = wp_remote_retrieve_body($response);
        $payload = json_decode($raw_body, true);
        if ($code < 200 || $code >= 300) {
            $message = 'Site Intelligence backend returned an error.';
            if (is_array($payload) && isset($payload['detail'])) {
                if (is_array($payload['detail']) && isset($payload['detail']['message'])) {
                    $message = sanitize_text_field($payload['detail']['message']);
                } elseif (is_string($payload['detail'])) {
                    $message = sanitize_text_field($payload['detail']);
                }
            } elseif (!empty($raw_body)) {
                $message = sanitize_text_field(wp_trim_words($raw_body, 24, '…'));
            }
            return new WP_Error('scsi_backend_error', $message, [
                'status' => $code,
                'payload' => $payload,
                'raw_body' => $raw_body,
            ]);
        }
        return is_array($payload) ? $payload : ['ok' => true, 'raw' => $raw_body];
    }

    public function rest_dashboard(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/dashboard' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_page(WP_REST_Request $request) {
        $path = sanitize_text_field($request->get_param('path'));
        $endpoint = 'intelligence/page?' . http_build_query(['path' => $path]);
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_ga4_diagnostics(WP_REST_Request $request) {
        $result = $this->backend_request('diagnostics/ga4');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_unmapped(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/unmapped' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_events(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/event-diagnostics' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_opportunities(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/page-opportunities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_conversions(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/conversions' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_external_health(WP_REST_Request $request) {
        $query = [];
        if ($request->get_param('force_refresh')) {
            $query['force_refresh'] = sanitize_text_field($request->get_param('force_refresh'));
        }
        $endpoint = 'external/health' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_external_cache(WP_REST_Request $request) {
        $result = $this->backend_request('external/cache');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_climate_energy(WP_REST_Request $request) {
        $query = [];
        foreach (['latitude', 'longitude', 'country', 'start', 'end', 'year', 'force_refresh'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/dashboards/climate-energy' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_search_intelligence(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        $endpoint = 'intelligence/search' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_search_opportunities(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'search/opportunities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_search_health(WP_REST_Request $request) {
        $result = $this->backend_request('search/health');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_metadata_intelligence(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'seo/metadata' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_internal_link_intelligence(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'seo/internal-links' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_seo_recommendations(WP_REST_Request $request) {
        $query = [];
        $start = $request->get_param('start_date') ?: $request->get_param('start');
        $end = $request->get_param('end_date') ?: $request->get_param('end');
        $limit = $request->get_param('limit');
        if (!empty($start)) { $query['start_date'] = sanitize_text_field($start); }
        if (!empty($end)) { $query['end_date'] = sanitize_text_field($end); }
        if (!empty($limit)) { $query['limit'] = sanitize_text_field($limit); }
        $endpoint = 'seo/recommendations' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }


    public function rest_indexing_intelligence(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'intelligence/indexing' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_sitemap_coverage(WP_REST_Request $request) {
        $result = $this->backend_request('indexing/sitemap');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_404_intelligence(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'indexing/404s' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_indexing_recommendations(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        $endpoint = 'indexing/recommendations' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    private function publishing_query_from_request(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'prior_start_date', 'prior_end_date', 'limit'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    public function rest_content_strategy(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/content-strategy' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_topic_momentum(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/topic-momentum' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_update_priorities(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/update-priorities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_publishing_opportunities(WP_REST_Request $request) {
        $query = $this->publishing_query_from_request($request);
        $endpoint = 'publishing/promotion-opportunities' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }


    private function public_query_from_request(WP_REST_Request $request) {
        $query = [];
        foreach (['start_date', 'end_date', 'latitude', 'longitude', 'country', 'start', 'end', 'year', 'live'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    public function rest_public_landing_page(WP_REST_Request $request) {
        $result = $this->backend_request('public/landing-page');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return $result;
    }

    public function rest_public_dashboard(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'public/dashboard' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_knowledge_overview(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'public/knowledge-overview' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_climate_energy_summary(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'public/climate-energy-summary' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_methodology(WP_REST_Request $request) {
        $result = $this->backend_request('public/methodology');
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function rest_public_readiness(WP_REST_Request $request) {
        $query = $this->public_query_from_request($request);
        $endpoint = 'intelligence/public-readiness' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }



    private function advanced_external_query_from_request(WP_REST_Request $request) {
        $query = [];
        foreach (['latitude', 'longitude', 'country', 'state', 'county', 'start', 'end', 'force_refresh'] as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    public function rest_advanced_external_health(WP_REST_Request $request) {
        $query = [];
        if ($request->get_param('force_refresh')) { $query['force_refresh'] = sanitize_text_field($request->get_param('force_refresh')); }
        $endpoint = 'external/advanced/health' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_environmental_monitoring(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/environmental-monitoring' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_urban_resilience(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/urban-resilience' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_biodiversity_land_use(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/biodiversity-land-use' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_energy_systems(WP_REST_Request $request) {
        $query = $this->advanced_external_query_from_request($request);
        $endpoint = 'intelligence/dashboards/energy-systems' . (!empty($query) ? '?' . http_build_query($query) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_event(WP_REST_Request $request) {
        $body = json_decode($request->get_body(), true);
        if (!is_array($body)) {
            $body = [];
        }
        $body['page_path'] = isset($body['page_path']) ? sanitize_text_field($body['page_path']) : '/';
        $body['event_name'] = isset($body['event_name']) ? sanitize_key($body['event_name']) : 'sc_unknown_event';
        $result = $this->backend_request('collect/event', 'POST', $body);
        if (is_wp_error($result)) {
            return $result;
        }
        return rest_ensure_response($result);
    }

    public function settings_page() {
        if (!current_user_can('manage_options')) {
            return;
        }
        $options = self::options();
        ?>
        <div class="wrap scsi-admin-wrap">
            <h1>Sustainable Catalyst Site Intelligence</h1>
            <p>Connect Sustainable Catalyst to the Site Intelligence backend and emit custom GA4/dataLayer events.</p>
            <form method="post" action="options.php">
                <?php settings_fields('sc_site_intelligence'); ?>
                <table class="form-table" role="presentation">
                    <tr>
                        <th scope="row"><label for="scsi_backend_url">Backend URL</label></th>
                        <td>
                            <input id="scsi_backend_url" type="url" class="regular-text" name="<?php echo esc_attr(self::OPTION_KEY); ?>[backend_url]" value="<?php echo esc_attr($options['backend_url']); ?>" placeholder="https://your-render-service.onrender.com" />
                            <p class="description">Do not include a trailing slash.</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row"><label for="scsi_api_token">API Token</label></th>
                        <td>
                            <input id="scsi_api_token" type="password" class="regular-text" name="<?php echo esc_attr(self::OPTION_KEY); ?>[api_token]" value="<?php echo esc_attr($options['api_token']); ?>" autocomplete="off" />
                            <p class="description">Stored in WordPress and sent server-side to the backend. It is not exposed to browser JavaScript.</p>
                        </td>
                    </tr>
                    <tr>
                        <th scope="row">Event Bridge</th>
                        <td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_KEY); ?>[enable_event_bridge]" value="1" <?php checked($options['enable_event_bridge'], '1'); ?> /> Emit Sustainable Catalyst custom events.</label></td>
                    </tr>
                    <tr>
                        <th scope="row">Shortcode Dashboard</th>
                        <td><label><input type="checkbox" name="<?php echo esc_attr(self::OPTION_KEY); ?>[enable_dashboard]" value="1" <?php checked($options['enable_dashboard'], '1'); ?> /> Enable dashboard shortcodes.</label></td>
                    </tr>
                </table>
                <?php submit_button(); ?>
            </form>
            <hr />
            <h2>Shortcodes</h2>
            <p><code>[sc_site_intelligence_dashboard]</code></p>
            <p><code>[sc_site_intelligence_page]</code></p>
            <p><code>[sc_site_intelligence_unmapped]</code></p>
            <p><code>[sc_site_intelligence_events]</code></p>
            <p><code>[sc_site_intelligence_opportunities]</code></p>
            <p><code>[sc_external_data_health]</code></p>
            <p><code>[sc_climate_energy_intelligence]</code></p>
            <p><code>[sc_external_cache_status]</code></p>
            <p><code>[sc_search_intelligence]</code></p>
            <p><code>[sc_search_opportunities]</code></p>
            <p><code>[sc_metadata_intelligence]</code></p>
            <p><code>[sc_internal_link_intelligence]</code></p>
            <p><code>[sc_seo_recommendations]</code></p>
            <p><code>[sc_indexing_intelligence]</code></p>
            <p><code>[sc_sitemap_coverage]</code></p>
            <p><code>[sc_404_intelligence]</code></p>
            <p><code>[sc_advanced_external_data_health]</code></p>
            <p><code>[sc_environmental_monitoring_intelligence]</code></p>
            <p><code>[sc_urban_resilience_intelligence]</code></p>
            <p><code>[sc_biodiversity_land_use_intelligence]</code></p>
            <p><code>[sc_energy_systems_intelligence]</code></p>
            <h2>Diagnostics</h2>
            <p>After saving settings, open <a href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/diagnostics/ga4')); ?>" target="_blank" rel="noopener">GA4 diagnostics</a> while logged in.</p>
        </div>
        <?php
    }

    public function enqueue_assets() {
        $options = self::options();
        $base = plugin_dir_url(__FILE__) . 'assets/';
        wp_enqueue_style('sc-site-intelligence', $base . 'sc-site-intelligence.css', [], self::VERSION);
        wp_enqueue_script('sc-site-intelligence', $base . 'sc-site-intelligence.js', [], self::VERSION, true);
        wp_localize_script('sc-site-intelligence', 'SCSiteIntelligence', [
            'restBase' => esc_url_raw(rest_url(self::REST_NAMESPACE)),
            'restNonce' => wp_create_nonce('wp_rest'),
            'enableEventBridge' => $options['enable_event_bridge'] === '1',
            'pagePath' => wp_parse_url(home_url(add_query_arg([])), PHP_URL_PATH),
            'pageTitle' => wp_get_document_title(),
            'siteUrl' => home_url('/'),
            'version' => self::VERSION,
        ]);
    }

    public function dashboard_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-dashboard" data-scsi-dashboard>
            <p class="scsi-eyebrow">Sustainable Catalyst Intelligence</p>
            <h2>Site Intelligence Dashboard</h2>
            <p class="scsi-muted">Loading analytics interpretation…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function page_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-page" data-scsi-page>
            <p class="scsi-eyebrow">Page Intelligence</p>
            <h2>This Page in the Knowledge System</h2>
            <p class="scsi-muted">Loading page-level analytics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function unmapped_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-unmapped" data-scsi-unmapped>
            <p class="scsi-eyebrow">Registry Intelligence</p>
            <h2>Unmapped and Inferred Pages</h2>
            <p class="scsi-muted">Loading registry mapping report…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function events_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-events" data-scsi-events>
            <p class="scsi-eyebrow">Conversion Validation</p>
            <h2>Event Tracking Diagnostics</h2>
            <p class="scsi-muted">Loading event diagnostics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function opportunities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-opportunities" data-scsi-opportunities>
            <p class="scsi-eyebrow">Conversion Opportunities</p>
            <h2>Page-Level CTA and Pathway Opportunities</h2>
            <p class="scsi-muted">Loading conversion opportunities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function external_health_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-external-health" data-scsi-external-health>
            <p class="scsi-eyebrow">External Data Intelligence</p>
            <h2>External Data Connector Health</h2>
            <p class="scsi-muted">Loading external connector status…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function climate_energy_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'start' => '',
            'end' => '',
            'year' => '',
        ], $atts, 'sc_climate_energy_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-climate-energy" data-scsi-climate-energy
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>"
            data-longitude="<?php echo esc_attr($atts['longitude']); ?>"
            data-country="<?php echo esc_attr($atts['country']); ?>"
            data-start="<?php echo esc_attr($atts['start']); ?>"
            data-end="<?php echo esc_attr($atts['end']); ?>"
            data-year="<?php echo esc_attr($atts['year']); ?>"
            data-live="<?php echo esc_attr($atts['live']); ?>">
            <p class="scsi-eyebrow">Climate + Energy Intelligence</p>
            <h2>Climate + Energy Intelligence Pilot</h2>
            <p class="scsi-muted">Loading NASA POWER, NASA GIBS, and Climate TRACE connector data…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function external_cache_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-external-cache" data-scsi-external-cache>
            <p class="scsi-eyebrow">External Data Cache</p>
            <h2>External Source Cache Status</h2>
            <p class="scsi-muted">Loading source cache status…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function search_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
        ], $atts, 'sc_search_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-search-intelligence" data-scsi-search-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Search Intelligence</p>
            <h2>Search Console and SEO Intelligence</h2>
            <p class="scsi-muted">Loading Search Console performance and Sustainable Catalyst SEO interpretation…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function search_opportunities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_search_opportunities');
        ob_start();
        ?>
        <section class="scsi-card scsi-search-opportunities" data-scsi-search-opportunities
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">SEO Opportunities</p>
            <h2>Search Opportunity Pages</h2>
            <p class="scsi-muted">Loading high-impression, low-CTR, and near-position opportunities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function metadata_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_metadata_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-metadata-intelligence" data-scsi-metadata-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Metadata Intelligence</p>
            <h2>Metadata, Titles, and CTR Review</h2>
            <p class="scsi-muted">Loading title, query alignment, and metadata review priorities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function internal_link_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_internal_link_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-internal-link-intelligence" data-scsi-internal-link-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Internal Link Intelligence</p>
            <h2>Internal Link and Pathway Opportunities</h2>
            <p class="scsi-muted">Loading internal-link priorities from Search Console and the registry…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function seo_recommendations_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_seo_recommendations');
        ob_start();
        ?>
        <section class="scsi-card scsi-seo-recommendations" data-scsi-seo-recommendations
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">SEO Recommendation Intelligence</p>
            <h2>Metadata and Internal-Link Action Queue</h2>
            <p class="scsi-muted">Loading combined metadata and internal-link recommendations…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    public function indexing_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
        ], $atts, 'sc_indexing_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-indexing-intelligence" data-scsi-indexing-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Indexing Intelligence</p>
            <h2>Sitemap, Indexing, and Registry Coverage</h2>
            <p class="scsi-muted">Loading sitemap, registry, GA4, and Search Console coverage…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function sitemap_coverage_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-sitemap-coverage" data-scsi-sitemap-coverage>
            <p class="scsi-eyebrow">Sitemap Coverage</p>
            <h2>XML Sitemap and Registry Alignment</h2>
            <p class="scsi-muted">Loading sitemap coverage…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function four_oh_four_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'limit' => '20',
        ], $atts, 'sc_404_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-404-intelligence" data-scsi-404-intelligence
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">404 Intelligence</p>
            <h2>404 and Routing Diagnostics</h2>
            <p class="scsi-muted">Loading 404 and routing diagnostics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    private function publishing_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'prior_start_date' => '',
            'prior_end_date' => '',
            'limit' => '20',
        ], $atts, $shortcode);
    }

    public function content_strategy_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_content_strategy_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-content-strategy" data-scsi-content-strategy
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Publishing Intelligence</p>
            <h2>Content Strategy and Publishing Intelligence</h2>
            <p class="scsi-muted">Loading publishing strategy signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function topic_momentum_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_topic_momentum');
        ob_start();
        ?>
        <section class="scsi-card scsi-topic-momentum" data-scsi-topic-momentum
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Topic Momentum</p>
            <h2>Article Map and Topic Momentum</h2>
            <p class="scsi-muted">Loading topic momentum and article-map performance…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function update_priorities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_update_priorities');
        ob_start();
        ?>
        <section class="scsi-card scsi-update-priorities" data-scsi-update-priorities
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Update Priorities</p>
            <h2>Content Decay, Rising Pages, and Update Queue</h2>
            <p class="scsi-muted">Loading update priorities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function publishing_opportunities_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->publishing_shortcode_atts($atts, 'sc_publishing_opportunities');
        ob_start();
        ?>
        <section class="scsi-card scsi-publishing-opportunities" data-scsi-publishing-opportunities
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start="<?php echo esc_attr($atts['prior_start_date']); ?>"
            data-prior-end="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>">
            <p class="scsi-eyebrow">Publishing Opportunities</p>
            <h2>Promotion, Newsletter, GitHub, and Tool Opportunities</h2>
            <p class="scsi-muted">Loading publishing promotion opportunities…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    private function public_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'start' => '',
            'end' => '',
            'year' => '',
            'live' => '',
        ], $atts, $shortcode);
    }


    public function public_landing_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-landing" data-scsi-public-landing>
            <p class="scsi-eyebrow">Sustainable Catalyst Site Intelligence</p>
            <h2>Public Dashboard Framework</h2>
            <p class="scsi-muted">Loading public Site Intelligence landing overview…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_site_intelligence_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_site_intelligence');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-dashboard" data-scsi-public-dashboard
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Public Site Intelligence</p>
            <h2>Sustainable Catalyst Public Intelligence Overview</h2>
            <p class="scsi-muted">Loading public-safe knowledge-system summary…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_knowledge_overview_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_knowledge_overview');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-knowledge-overview" data-scsi-public-knowledge-overview
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Knowledge-System Overview</p>
            <h2>Knowledge Areas and Public Surfaces</h2>
            <p class="scsi-muted">Loading public-safe knowledge-area overview…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_climate_energy_summary_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_climate_energy_summary');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-climate-energy" data-scsi-public-climate-energy
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>"
            data-longitude="<?php echo esc_attr($atts['longitude']); ?>"
            data-country="<?php echo esc_attr($atts['country']); ?>"
            data-start="<?php echo esc_attr($atts['start']); ?>"
            data-end="<?php echo esc_attr($atts['end']); ?>"
            data-year="<?php echo esc_attr($atts['year']); ?>"
            data-live="<?php echo esc_attr($atts['live']); ?>">
            <p class="scsi-eyebrow">Climate + Energy Public Summary</p>
            <h2>Climate, Energy, and External Source Snapshot</h2>
            <p class="scsi-muted">Loading public-safe climate and energy summary…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_methodology_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-methodology" data-scsi-public-methodology>
            <p class="scsi-eyebrow">Public Dashboard Methodology</p>
            <h2>What Public Site Intelligence Shows and Hides</h2>
            <p class="scsi-muted">Loading public methodology and source notes…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_dashboard_readiness_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = $this->public_shortcode_atts($atts, 'sc_public_dashboard_readiness');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-readiness" data-scsi-public-readiness
            data-start="<?php echo esc_attr($atts['start_date']); ?>"
            data-end="<?php echo esc_attr($atts['end_date']); ?>">
            <p class="scsi-eyebrow">Public Dashboard Readiness</p>
            <h2>Internal Public-Release Checklist</h2>
            <p class="scsi-muted">Loading public-readiness diagnostics…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }


    private function advanced_external_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'state' => '',
            'county' => '',
            'start' => '',
            'end' => '',
            'force_refresh' => '',
        ], $atts, $shortcode);
    }

    public function advanced_external_health_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-advanced-external-health" data-scsi-advanced-external-health>
            <p class="scsi-eyebrow">Advanced External Data</p>
            <h2>Advanced External Connector Health</h2>
            <p class="scsi-muted">Loading NOAA, EIA, EPA, Census, USGS, and GBIF connector health…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function environmental_monitoring_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_environmental_monitoring_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-environmental-monitoring" data-scsi-environmental-monitoring
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-state="<?php echo esc_attr($atts['state']); ?>" data-county="<?php echo esc_attr($atts['county']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Environmental Monitoring</p>
            <h2>Environmental Monitoring Intelligence</h2>
            <p class="scsi-muted">Loading environmental monitoring signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function urban_resilience_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_urban_resilience_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-urban-resilience" data-scsi-urban-resilience
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-country="<?php echo esc_attr($atts['country']); ?>" data-state="<?php echo esc_attr($atts['state']); ?>" data-county="<?php echo esc_attr($atts['county']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Urban Resilience</p>
            <h2>Urban Resilience Intelligence</h2>
            <p class="scsi-muted">Loading urban resilience signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function biodiversity_land_use_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_biodiversity_land_use_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-biodiversity-land-use" data-scsi-biodiversity-land-use
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-country="<?php echo esc_attr($atts['country']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Biodiversity + Land Use</p>
            <h2>Biodiversity and Land Use Intelligence</h2>
            <p class="scsi-muted">Loading biodiversity and land-use signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function energy_systems_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->advanced_external_shortcode_atts($atts, 'sc_energy_systems_intelligence');
        ob_start(); ?>
        <section class="scsi-card scsi-energy-systems" data-scsi-energy-systems
            data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>" data-country="<?php echo esc_attr($atts['country']); ?>" data-state="<?php echo esc_attr($atts['state']); ?>" data-start="<?php echo esc_attr($atts['start']); ?>" data-end="<?php echo esc_attr($atts['end']); ?>" data-force-refresh="<?php echo esc_attr($atts['force_refresh']); ?>">
            <p class="scsi-eyebrow">Energy Systems</p>
            <h2>Energy Systems Data Intelligence</h2>
            <p class="scsi-muted">Loading energy systems signals…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

}

new SC_Site_Intelligence_Plugin();
