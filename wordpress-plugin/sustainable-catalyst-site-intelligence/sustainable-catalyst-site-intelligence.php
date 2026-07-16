<?php
/**
 * Plugin Name: Sustainable Catalyst Site Intelligence
 * Description: Embeds the Sustainable Catalyst Auditable Public Observatory and its source-aware public intelligence workspaces.
 * Version: 2.12.0
 * Author: Content Catalyst LLC
 * License: MIT
 */

if (!defined('ABSPATH')) {
    exit;
}

final class SC_Site_Intelligence_Plugin {
    const OPTION_KEY = 'sc_site_intelligence_options';
    const VERSION = '2.12.0';
    const REST_NAMESPACE = 'sc-site-intelligence/v1';
    const BUILD_INFO_STATUS_OPTION = 'scsi_build_info_status';
    const INSTALLED_VERSION_OPTION = 'scsi_installed_plugin_version';
    const BUILD_INFO_MATCH_TTL = 21600;
    const BUILD_INFO_MISMATCH_TTL = 45;
    const BUILD_INFO_ERROR_TTL = 30;
    const LEGACY_SHORTCODE_REMOVAL_TARGET = 'fulfilled-in-2.0.0';
    const LEGACY_SHORTCODE_COMPATIBILITY = 'modern-workspace-aliases';

    public function __construct() {
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_init', [$this, 'register_settings']);
        add_action('admin_init', [$this, 'maybe_upgrade']);
        add_action('admin_post_scsi_refresh_backend_version', [$this, 'handle_refresh_backend_version']);
        add_action('admin_notices', [$this, 'backend_version_notice']);
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
        add_shortcode('sc_site_intelligence_public_flagship', [$this, 'public_flagship_shortcode']);
        add_shortcode('sc_site_intelligence_public_page_builder', [$this, 'public_page_builder_shortcode']);
        add_shortcode('sc_public_dashboard_shortcode_bundle', [$this, 'public_shortcode_bundle_shortcode']);
        add_shortcode('sc_public_dashboard_visual_qa', [$this, 'public_visual_qa_shortcode']);
        add_shortcode('sc_public_site_intelligence', [$this, 'public_site_intelligence_shortcode']);
        add_shortcode('sc_public_knowledge_overview', [$this, 'public_knowledge_overview_shortcode']);
        add_shortcode('sc_public_climate_energy_summary', [$this, 'public_climate_energy_summary_shortcode']);
        add_shortcode('sc_public_methodology', [$this, 'public_methodology_shortcode']);
        add_shortcode('sc_public_dashboard_directory', [$this, 'public_dashboard_directory_shortcode']);
        add_shortcode('sc_public_dashboard_navigation', [$this, 'public_dashboard_navigation_shortcode']);
        add_shortcode('sc_public_topic_page_templates', [$this, 'public_topic_page_templates_shortcode']);
        add_shortcode('sc_public_topic_page_visual_qa', [$this, 'public_topic_page_visual_qa_shortcode']);
        add_shortcode('sc_public_api_sources', [$this, 'public_api_sources_shortcode']);
        add_shortcode('sc_public_source_health', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_development_indicators', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_research_metadata', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_publication_metadata', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_repository_intelligence', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_indicator_overview', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_sustainability_indicators', [$this, 'public_source_panel_shortcode']);
        add_shortcode('sc_public_source_page_directory', [$this, 'public_source_page_directory_shortcode']);
        add_shortcode('sc_public_source_navigation', [$this, 'public_source_navigation_shortcode']);
        add_shortcode('sc_public_source_page_templates', [$this, 'public_source_page_templates_shortcode']);
        add_shortcode('sc_public_source_page_visual_qa', [$this, 'public_source_page_visual_qa_shortcode']);
        add_shortcode('sc_public_connector_status', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_cache_status', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_source_freshness', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_connector_reliability', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_connector_status_polish', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_world_bank_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_openalex_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_crossref_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_github_connector', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_environmental_connectors', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_sources', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_families', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_planetary_boundaries_registry', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_source_health', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_methodology', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_connector_reliability', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_freshness', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_schema_validation', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_sustainable_development_cache_status', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_planetary_boundaries_observatory', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_planetary_boundary_overview', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_planetary_boundary', [$this, 'planetary_boundary_shortcode']);
        add_shortcode('sc_planetary_boundary_trend', [$this, 'planetary_boundary_trend_shortcode']);
        add_shortcode('sc_planetary_boundary_sources', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_planetary_boundary_methodology', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_planetary_boundary_export', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_humanitarian_intelligence_observatory', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_global_crisis_map', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_humanitarian_report_stream', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_displacement_context', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_humanitarian_intelligence_sources', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_humanitarian_intelligence_methodology', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_humanitarian_intelligence_export', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_development_observatory', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_development_sources', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_development_domain', [$this, 'human_development_domain_shortcode']);
        add_shortcode('sc_human_development_country_profile', [$this, 'human_development_country_profile_shortcode']);
        add_shortcode('sc_human_development_inequalities', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_development_methodology', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_development_export', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_international_law_governance_monitor', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_international_law_sources', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_un_sanctions_monitor', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_international_law_event_stream', [$this, 'international_law_event_stream_shortcode']);
        add_shortcode('sc_international_law_monitor', [$this, 'international_law_monitor_shortcode']);
        add_shortcode('sc_international_law_methodology', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_international_law_export', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_conflict_human_security_monitor', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_security_sources', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_conflict_event_stream', [$this, 'human_security_event_stream_shortcode']);
        add_shortcode('sc_human_security_monitor', [$this, 'human_security_monitor_shortcode']);
        add_shortcode('sc_forced_displacement_flows', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_modeled_human_security_risk', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_security_methodology', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_human_security_export', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_dashboard_studio', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_dashboard_launch_manifest', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_dashboard_launch_readiness', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_dashboard_studio_navigation', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_site_intelligence_app', [$this, 'standalone_app_shortcode']);
        add_shortcode('sc_auditable_public_observatory', [$this, 'auditable_public_observatory_shortcode']);
        add_shortcode('sc_site_intelligence_launch', [$this, 'site_intelligence_launch_shortcode']);
        add_shortcode('sc_earth_observation_studio', [$this, 'earth_observation_studio_shortcode']);
        add_shortcode('sc_live_event_intelligence', [$this, 'live_event_intelligence_shortcode']);
        add_shortcode('sc_global_country_intelligence', [$this, 'global_country_intelligence_shortcode']);
        add_shortcode('sc_comparative_intelligence', [$this, 'comparative_intelligence_shortcode']);
        add_shortcode('sc_public_briefing_studio', [$this, 'public_briefing_studio_shortcode']);
        add_shortcode('sc_thematic_intelligence', [$this, 'thematic_intelligence_shortcode']);
        add_shortcode('sc_source_methodology_studio', [$this, 'source_methodology_studio_shortcode']);
        add_shortcode('sc_saved_research_views', [$this, 'saved_research_views_shortcode']);
        add_shortcode('sc_geospatial_intelligence_map', [$this, 'geospatial_map_shortcode']);
        add_shortcode('sc_satellite_imagery_viewer', [$this, 'geospatial_map_shortcode']);
        add_shortcode('sc_live_event_map', [$this, 'geospatial_map_shortcode']);
        add_shortcode('sc_geospatial_accessible_table', [$this, 'geospatial_table_shortcode']);
        add_shortcode('sc_geospatial_layer_directory', [$this, 'geospatial_layer_directory_shortcode']);
        add_shortcode('sc_public_cross_domain_dashboard_directory', [$this, 'public_connector_panel_shortcode']);
        add_shortcode('sc_public_intelligence_dashboard', [$this, 'cross_domain_dashboard_shortcode']);
        add_shortcode('sc_public_country_intelligence', [$this, 'country_intelligence_shortcode']);
        add_shortcode('sc_public_cross_domain_comparison', [$this, 'cross_domain_comparison_shortcode']);
        add_shortcode('sc_public_dashboard_sources', [$this, 'cross_domain_dashboard_sources_shortcode']);
        add_shortcode('sc_public_dashboard_export', [$this, 'cross_domain_dashboard_export_shortcode']);
        add_shortcode('sc_public_indicator_dashboard_directory', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_sustainability_indicator_dashboard', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_development_indicator_dashboard', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_source_health_chart_dashboard', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_research_metadata_chart_dashboard', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_repository_chart_dashboard', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_indicator_chart_gallery', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_indicator_chart_visual_qa', [$this, 'public_indicator_chart_panel_shortcode']);
        add_shortcode('sc_public_source_aware_brief_directory', [$this, 'public_source_aware_brief_panel_shortcode']);
        add_shortcode('sc_public_site_intelligence_source_brief', [$this, 'public_source_aware_brief_panel_shortcode']);
        add_shortcode('sc_public_indicator_source_brief', [$this, 'public_source_aware_brief_panel_shortcode']);
        add_shortcode('sc_public_source_health_brief', [$this, 'public_source_aware_brief_panel_shortcode']);
        add_shortcode('sc_public_dashboard_export_manifest', [$this, 'public_dashboard_export_panel_shortcode']);
        add_shortcode('sc_public_site_intelligence_export', [$this, 'public_dashboard_export_panel_shortcode']);
        add_shortcode('sc_public_indicator_dashboard_export', [$this, 'public_dashboard_export_panel_shortcode']);
        add_shortcode('sc_public_source_health_export', [$this, 'public_dashboard_export_panel_shortcode']);
        add_shortcode('sc_public_dashboard_export_visual_qa', [$this, 'public_dashboard_export_panel_shortcode']);
        add_shortcode('sc_public_climate_energy_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_environmental_monitoring_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_biodiversity_land_use_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_knowledge_system_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_search_discovery_dashboard', [$this, 'public_topic_dashboard_shortcode']);
        add_shortcode('sc_public_source_methodology', [$this, 'public_source_methodology_shortcode']);
        add_shortcode('sc_public_dashboard_readiness', [$this, 'public_dashboard_readiness_shortcode']);
        add_shortcode('sc_advanced_external_data_health', [$this, 'advanced_external_health_shortcode']);
        add_shortcode('sc_environmental_monitoring_intelligence', [$this, 'environmental_monitoring_shortcode']);
        add_shortcode('sc_urban_resilience_intelligence', [$this, 'urban_resilience_shortcode']);
        add_shortcode('sc_biodiversity_land_use_intelligence', [$this, 'biodiversity_land_use_shortcode']);
        add_shortcode('sc_energy_systems_intelligence', [$this, 'energy_systems_shortcode']);
        add_shortcode('sc_site_intelligence_report', [$this, 'site_intelligence_report_shortcode']);
        add_shortcode('sc_search_intelligence_report', [$this, 'search_intelligence_report_shortcode']);
        add_shortcode('sc_content_strategy_report', [$this, 'content_strategy_report_shortcode']);
        add_shortcode('sc_external_sources_report', [$this, 'external_sources_report_shortcode']);
        add_shortcode('sc_climate_energy_report', [$this, 'climate_energy_report_shortcode']);
        add_shortcode('sc_indexing_report', [$this, 'indexing_report_shortcode']);
        add_shortcode('sc_report_export_bundle', [$this, 'report_export_bundle_shortcode']);
        add_shortcode('sc_ai_brief_status', [$this, 'ai_brief_status_shortcode']);
        add_shortcode('sc_ai_site_intelligence_brief', [$this, 'ai_site_intelligence_brief_shortcode']);
        add_shortcode('sc_ai_search_brief', [$this, 'ai_search_brief_shortcode']);
        add_shortcode('sc_ai_publishing_brief', [$this, 'ai_publishing_brief_shortcode']);
        add_shortcode('sc_ai_external_sources_brief', [$this, 'ai_external_sources_brief_shortcode']);
        add_shortcode('sc_ai_public_dashboard_brief', [$this, 'ai_public_dashboard_brief_shortcode']);
        add_shortcode('sc_site_intelligence_admin_overview', [$this, 'admin_overview_shortcode']);
        add_shortcode('sc_site_intelligence_shortcode_catalog', [$this, 'shortcode_catalog_shortcode']);
        add_shortcode('sc_site_intelligence_module_status', [$this, 'module_status_shortcode']);
        add_shortcode('sc_site_intelligence_diagnostic_summary', [$this, 'diagnostic_summary_shortcode']);
        add_shortcode('sc_site_intelligence_connection_check', [$this, 'connection_check_shortcode']);
        add_shortcode('sc_site_intelligence_release_status', [$this, 'release_status_shortcode']);
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

    public static function activate() {
        self::clear_all_build_info_cache();
        delete_option(self::BUILD_INFO_STATUS_OPTION);
        update_option(self::INSTALLED_VERSION_OPTION, self::VERSION, false);
    }

    public function maybe_upgrade() {
        $installed = sanitize_text_field((string) get_option(self::INSTALLED_VERSION_OPTION, ''));
        if ($installed === self::VERSION) {
            return;
        }

        self::clear_all_build_info_cache();
        delete_option(self::BUILD_INFO_STATUS_OPTION);
        update_option(self::INSTALLED_VERSION_OPTION, self::VERSION, false);
    }

    private static function build_info_cache_key($backend) {
        $backend = untrailingslashit((string) $backend);
        return 'scsi_build_info_' . md5($backend . '|' . self::VERSION);
    }

    private static function legacy_build_info_cache_key($backend) {
        return 'scsi_build_info_' . md5(untrailingslashit((string) $backend));
    }

    private static function clear_backend_build_info_cache($backend) {
        $backend = untrailingslashit((string) $backend);
        if ($backend === '') {
            return;
        }

        delete_transient(self::build_info_cache_key($backend));
        delete_transient(self::legacy_build_info_cache_key($backend));
    }

    public static function clear_all_build_info_cache() {
        global $wpdb;

        $patterns = [
            $wpdb->esc_like('_transient_scsi_build_info_') . '%',
            $wpdb->esc_like('_transient_timeout_scsi_build_info_') . '%',
        ];

        foreach ($patterns as $pattern) {
            $names = $wpdb->get_col(
                $wpdb->prepare(
                    "SELECT option_name FROM {$wpdb->options} WHERE option_name LIKE %s",
                    $pattern
                )
            );

            foreach ((array) $names as $name) {
                delete_option($name);
            }
        }
    }

    private function backend_version_refresh_url() {
        return wp_nonce_url(
            admin_url('admin-post.php?action=scsi_refresh_backend_version'),
            'scsi_refresh_backend_version'
        );
    }

    private function store_backend_version_status($status, $ttl) {
        $status = is_array($status) ? $status : [];
        $status['plugin_version'] = self::VERSION;
        $status['checked_at'] = gmdate('c');
        $status['ttl_seconds'] = (int) $ttl;

        $backend = untrailingslashit((string) ($status['backend_url'] ?? ''));
        if ($backend !== '') {
            set_transient(self::build_info_cache_key($backend), $status, (int) $ttl);
        }
        update_option(self::BUILD_INFO_STATUS_OPTION, $status, false);
        return $status;
    }

    private function verify_backend_version($force = false) {
        $options = self::options();
        $backend = untrailingslashit((string) ($options['backend_url'] ?? ''));

        if ($backend === '') {
            return [
                'state' => 'not-configured',
                'backend_url' => '',
                'plugin_version' => self::VERSION,
                'backend_version' => '',
                'expected_wordpress_plugin_version' => '',
                'http_status' => 0,
                'message' => 'No backend URL is configured.',
                'checked_at' => gmdate('c'),
            ];
        }

        $cache_key = self::build_info_cache_key($backend);
        if (!$force) {
            $cached = get_transient($cache_key);
            if (is_array($cached)) {
                return $cached;
            }
        }

        self::clear_backend_build_info_cache($backend);

        $endpoint = add_query_arg([
            'plugin_version' => self::VERSION,
            'cache_bust' => (string) time(),
        ], $backend . '/public/build-info');

        $response = wp_remote_get($endpoint, [
            'timeout' => 6,
            'redirection' => 2,
            'headers' => [
                'Accept' => 'application/json',
                'Cache-Control' => 'no-cache',
                'User-Agent' => 'Sustainable-Catalyst-Site-Intelligence/' . self::VERSION,
            ],
        ]);

        if (is_wp_error($response)) {
            return $this->store_backend_version_status([
                'state' => 'unavailable',
                'backend_url' => $backend,
                'backend_version' => '',
                'expected_wordpress_plugin_version' => '',
                'http_status' => 0,
                'message' => sanitize_text_field($response->get_error_message()),
            ], self::BUILD_INFO_ERROR_TTL);
        }

        $code = (int) wp_remote_retrieve_response_code($response);
        $payload = json_decode(wp_remote_retrieve_body($response), true);

        if ($code < 200 || $code >= 300 || !is_array($payload)) {
            return $this->store_backend_version_status([
                'state' => 'invalid-response',
                'backend_url' => $backend,
                'backend_version' => '',
                'expected_wordpress_plugin_version' => '',
                'http_status' => $code,
                'message' => 'The build-info endpoint did not return a valid JSON response.',
            ], self::BUILD_INFO_ERROR_TTL);
        }

        $backend_version = sanitize_text_field((string) ($payload['backend_version'] ?? $payload['version'] ?? ''));
        $expected_plugin = sanitize_text_field((string) ($payload['expected_wordpress_plugin_version'] ?? ''));

        if ($backend_version === '') {
            return $this->store_backend_version_status([
                'state' => 'invalid-response',
                'backend_url' => $backend,
                'backend_version' => '',
                'expected_wordpress_plugin_version' => $expected_plugin,
                'http_status' => $code,
                'message' => 'The build-info response did not include a backend version.',
            ], self::BUILD_INFO_ERROR_TTL);
        }

        $matches = $backend_version === self::VERSION
            && ($expected_plugin === '' || $expected_plugin === self::VERSION);

        return $this->store_backend_version_status([
            'state' => $matches ? 'match' : 'mismatch',
            'backend_url' => $backend,
            'backend_version' => $backend_version,
            'expected_wordpress_plugin_version' => $expected_plugin,
            'http_status' => $code,
            'message' => $matches
                ? 'The WordPress plugin and backend versions match.'
                : 'The WordPress plugin and backend versions do not match.',
        ], $matches ? self::BUILD_INFO_MATCH_TTL : self::BUILD_INFO_MISMATCH_TTL);
    }

    public function handle_refresh_backend_version() {
        if (!current_user_can('manage_options')) {
            wp_die(esc_html__('You are not allowed to refresh Site Intelligence status.', 'sc-site-intelligence'));
        }

        check_admin_referer('scsi_refresh_backend_version');

        $options = self::options();
        self::clear_backend_build_info_cache((string) ($options['backend_url'] ?? ''));
        delete_option(self::BUILD_INFO_STATUS_OPTION);
        $status = $this->verify_backend_version(true);

        $redirect = add_query_arg([
            'page' => 'sc-site-intelligence',
            'scsi_version_refreshed' => '1',
            'scsi_version_state' => sanitize_key((string) ($status['state'] ?? 'unknown')),
        ], admin_url('options-general.php'));

        wp_safe_redirect($redirect);
        exit;
    }

    public function backend_version_notice() {
        if (!current_user_can('manage_options')) {
            return;
        }

        $status = $this->verify_backend_version(false);
        $state = sanitize_key((string) ($status['state'] ?? ''));
        if ($state === 'match' || $state === 'not-configured') {
            return;
        }

        $backend = sanitize_text_field((string) ($status['backend_version'] ?? ''));
        $checked = sanitize_text_field((string) ($status['checked_at'] ?? ''));
        $refresh_url = $this->backend_version_refresh_url();

        if ($state === 'mismatch') {
            echo '<div class="notice notice-warning"><p><strong>Site Intelligence version mismatch.</strong> ';
            echo 'WordPress plugin: <code>' . esc_html(self::VERSION) . '</code>; backend: <code>' . esc_html($backend !== '' ? $backend : 'unknown') . '</code>. ';
            echo 'This mismatch is rechecked automatically after ' . esc_html((string) self::BUILD_INFO_MISMATCH_TTL) . ' seconds. ';
            echo '<a href="' . esc_url($refresh_url) . '">Refresh backend version now</a>';
            if ($checked !== '') {
                echo ' <span class="description">Last checked: ' . esc_html($checked) . '</span>';
            }
            echo '</p></div>';
            return;
        }

        $label = $state === 'invalid-response'
            ? 'Site Intelligence returned an invalid build-info response.'
            : 'Site Intelligence backend verification is temporarily unavailable.';
        echo '<div class="notice notice-info"><p><strong>' . esc_html($label) . '</strong> ';
        echo 'The public application can remain available while the version check is retried. ';
        echo '<a href="' . esc_url($refresh_url) . '">Refresh backend version now</a></p></div>';
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
        $current = self::options();
        $output = [];
        $output['backend_url'] = isset($input['backend_url']) ? esc_url_raw(trim($input['backend_url'])) : $defaults['backend_url'];
        $output['api_token'] = isset($input['api_token']) ? sanitize_text_field($input['api_token']) : $defaults['api_token'];
        $output['enable_event_bridge'] = !empty($input['enable_event_bridge']) ? '1' : '0';
        $output['enable_dashboard'] = !empty($input['enable_dashboard']) ? '1' : '0';

        self::clear_backend_build_info_cache((string) ($current['backend_url'] ?? ''));
        self::clear_backend_build_info_cache((string) ($output['backend_url'] ?? ''));
        delete_option(self::BUILD_INFO_STATUS_OPTION);

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
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder-shortcodes', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder_shortcodes'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder-readiness', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder_readiness'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-page-builder-visual-qa', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_page_builder_visual_qa'],
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

        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-directory', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard_directory'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-topic-dashboard', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_topic_dashboard'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-methodology', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_methodology'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-navigation', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard_navigation'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-topic-page-templates', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_topic_page_templates'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-topic-page-visual-qa', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_topic_page_visual_qa'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-api-sources', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_api_sources'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-health', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_health'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-development-indicators', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_development_indicators'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-research-metadata', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_research_metadata'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-publication-metadata', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_publication_metadata'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-repository-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_repository_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-indicator-overview', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_indicator_overview'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainability-indicators', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_sustainability_indicators'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-pages', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_pages'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-navigation', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_navigation'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-page-templates', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_page_templates'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-page-visual-qa', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_page_visual_qa'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-connector-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_connector_status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-cache-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_cache_status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-source-freshness', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_freshness'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-connector-reliability', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_connector_reliability'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-connector-status-polish', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_connector_status_polish'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-connector-detail', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_connector_detail'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-sources', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_sources'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-families', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_families'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundaries-registry', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundaries_registry'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-source-health', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_source_health'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-methodology', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_methodology'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-connector-reliability', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_connector_reliability'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-freshness', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_freshness'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-schema-validation', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_schema_validation'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-sustainable-development-cache-status', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_sustainable_development_cache_status'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundaries-observatory', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundaries_observatory'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundary', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundary'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundary-trend', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundary_trend'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundary-sources', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundary_sources'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundary-methodology', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundary_methodology'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-planetary-boundary-export', [
            'methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_planetary_boundary_export'], 'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-humanitarian-intelligence', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_humanitarian_intelligence'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-humanitarian-crisis-map', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_humanitarian_crisis_map'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-humanitarian-reports', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_humanitarian_reports'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-displacement-context', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_displacement_context'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-humanitarian-intelligence-sources', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_humanitarian_sources'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-humanitarian-intelligence-methodology', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_humanitarian_methodology'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-humanitarian-intelligence-export', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_humanitarian_export'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development-sources', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development_sources'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development-domain', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development_domain'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development-country-profile', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development_country_profile'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development-inequalities', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development_inequalities'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development-methodology', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development_methodology'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-development-export', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_development_export'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law-sources', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law_sources'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law-sanctions', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law_sanctions'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law-events', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law_events'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law-monitor', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law_monitor'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law-methodology', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law_methodology'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-international-law-export', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_international_law_export'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-sources', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_sources'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-events', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_events'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-monitor', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_monitor'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-displacement', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_displacement'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-modeled-risk', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_modeled_risk'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-methodology', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_methodology'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-human-security-export', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_human_security_export'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-geospatial', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_geospatial'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-geospatial-layers', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_geospatial_layers'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-geospatial-events', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_geospatial_events'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-geospatial-heatmap', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_geospatial_heatmap'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-geospatial-satellite', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_geospatial_satellite'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-geospatial-accessibility', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_geospatial_accessibility'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-cross-domain-dashboards', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_cross_domain_dashboards'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-cross-domain-dashboard-manifest', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_cross_domain_dashboard_manifest'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-launch-manifest', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_dashboard_launch_manifest'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-launch-readiness', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_dashboard_launch_readiness'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-studio-navigation', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_dashboard_studio_navigation'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-cross-domain-dashboard', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_cross_domain_dashboard'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-cross-domain-dashboard-sources', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_cross_domain_dashboard_sources'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-cross-domain-dashboard-export', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_cross_domain_dashboard_export'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-country-intelligence', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_country_intelligence'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-cross-domain-comparison', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_cross_domain_comparison'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-rendering-diagnostics', ['methods' => WP_REST_Server::READABLE, 'callback' => [$this, 'rest_public_dashboard_rendering_diagnostics'], 'permission_callback' => '__return_true']);
        register_rest_route(self::REST_NAMESPACE, '/public-indicator-chart-panel', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_indicator_chart_panel'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/public-source-aware-brief-panel', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_source_aware_brief_panel'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/public-dashboard-export-panel', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_public_dashboard_export_panel'],
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

        register_rest_route(self::REST_NAMESPACE, '/report-site-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_site_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-search-intelligence', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_search_intelligence'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-content-strategy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_content_strategy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-external-sources', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_external_sources'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-climate-energy', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_climate_energy'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-indexing', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_indexing'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/report-export', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_report_export'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/reports-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_reports_summary'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/ai-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-site-intelligence-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_site_intelligence_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-search-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_search_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-publishing-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_publishing_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-external-sources-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_external_sources_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-public-dashboard-brief', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_public_dashboard_brief'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route(self::REST_NAMESPACE, '/ai-briefs-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_ai_briefs_summary'],
            'permission_callback' => '__return_true',
        ]);

        register_rest_route(self::REST_NAMESPACE, '/admin-overview', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_overview'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-registry', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_registry'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-sources', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_sources'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-modules', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_modules'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-shortcodes', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_shortcodes'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-diagnostics', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_diagnostics'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-visibility', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_visibility'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-source-control', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_source_control'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_status'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-connection-check', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_connection_check'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-public-readiness-check', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_public_readiness_check'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/admin-diagnostic-summary', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_admin_diagnostic_summary'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/release-status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_release_status'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
        ]);
        register_rest_route(self::REST_NAMESPACE, '/release-smoke-test', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [$this, 'rest_release_smoke_test'],
            'permission_callback' => function () { return current_user_can('manage_options'); },
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

    private function safe_backend_error_message($raw_body, $fallback = 'Site Intelligence backend returned an error.') {
        $raw_body = is_string($raw_body) ? $raw_body : '';
        if ($raw_body === '') {
            return $fallback;
        }
        if (stripos($raw_body, '<!DOCTYPE') !== false || stripos($raw_body, '<html') !== false || stripos($raw_body, 'cloudflare') !== false || stripos($raw_body, 'bad gateway') !== false) {
            return 'Site Intelligence backend or site proxy returned a gateway error. Try the direct Render endpoint, then redeploy or retry the WordPress proxy after the origin is healthy.';
        }
        return sanitize_text_field(wp_trim_words(wp_strip_all_tags($raw_body), 24, '…'));
    }

    private function backend_request($endpoint, $method = 'GET', $body = null) {
        $options = self::options();
        if (empty($options['backend_url'])) {
            return new WP_Error('scsi_no_backend', 'Site Intelligence backend URL is not configured.', ['status' => 400]);
        }

        $url = untrailingslashit($options['backend_url']) . '/' . ltrim($endpoint, '/');
        $method = strtoupper($method);
        $is_cacheable = ($method === 'GET' && is_null($body));
        $cache_hash = md5($url);
        $fresh_key = 'scsi_fresh_' . $cache_hash;
        $stale_key = 'scsi_stale_' . $cache_hash;

        if ($is_cacheable) {
            $fresh = get_transient($fresh_key);
            if (is_array($fresh)) {
                $fresh['_scsi_delivery'] = [
                    'mode' => 'cache',
                    'freshness' => 'fresh',
                ];
                return $fresh;
            }
        }

        $args = [
            'method' => $method,
            'timeout' => 45,
            'redirection' => 3,
            'headers' => [
                'Accept' => 'application/json',
                'Content-Type' => 'application/json',
                'User-Agent' => 'Sustainable-Catalyst-Site-Intelligence/' . self::VERSION,
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
            if ($is_cacheable) {
                $stale = get_transient($stale_key);
                if (is_array($stale)) {
                    $stale['_scsi_delivery'] = [
                        'mode' => 'stale_cache',
                        'freshness' => 'stale',
                        'reason' => sanitize_text_field($response->get_error_message()),
                    ];
                    return $stale;
                }
            }
            return $response;
        }

        $code = wp_remote_retrieve_response_code($response);
        $raw_body = wp_remote_retrieve_body($response);
        $payload = json_decode($raw_body, true);
        if ($code < 200 || $code >= 300) {
            if ($is_cacheable) {
                $stale = get_transient($stale_key);
                if (is_array($stale)) {
                    $stale['_scsi_delivery'] = [
                        'mode' => 'stale_cache',
                        'freshness' => 'stale',
                        'reason' => 'Origin returned HTTP ' . intval($code),
                    ];
                    return $stale;
                }
            }
            $message = 'Site Intelligence backend returned an error.';
            if (is_array($payload) && isset($payload['detail'])) {
                if (is_array($payload['detail']) && isset($payload['detail']['message'])) {
                    $message = sanitize_text_field($payload['detail']['message']);
                } elseif (is_string($payload['detail'])) {
                    $message = sanitize_text_field($payload['detail']);
                }
            } elseif (!empty($raw_body)) {
                $message = $this->safe_backend_error_message($raw_body);
            }
            return new WP_Error('scsi_backend_error', $message, [
                'status' => $code,
                'payload' => is_array($payload) ? $payload : null,
            ]);
        }

        $result = is_array($payload) ? $payload : ['ok' => true, 'raw' => $raw_body];
        if ($is_cacheable) {
            set_transient($fresh_key, $result, 5 * MINUTE_IN_SECONDS);
            set_transient($stale_key, $result, 6 * HOUR_IN_SECONDS);
        }
        $result['_scsi_delivery'] = [
            'mode' => 'origin',
            'freshness' => 'fresh',
        ];
        return $result;
    }


    public function rest_public_sustainable_development_sources() { return $this->backend_request('public/sustainable-development/sources'); }
    public function rest_public_sustainable_development_families() { return $this->backend_request('public/sustainable-development/families'); }
    public function rest_public_planetary_boundaries_registry() { return $this->backend_request('public/sustainable-development/planetary-boundaries'); }
    public function rest_public_sustainable_development_source_health(WP_REST_Request $request) {
        $live = $request->get_param('live') ? '?live=true' : '';
        return $this->backend_request('public/sustainable-development/health' . $live);
    }
    public function rest_public_sustainable_development_methodology() { return $this->backend_request('public/sustainable-development/methodology'); }
    public function rest_public_sustainable_development_connector_reliability(WP_REST_Request $request) {
        $query = [];
        if ($request->get_param('live')) { $query['live'] = 'true'; }
        if ($request->get_param('force')) { $query['force'] = 'true'; }
        return $this->backend_request('public/sustainable-development/reliability' . (!empty($query) ? '?' . http_build_query($query) : ''));
    }
    public function rest_public_sustainable_development_freshness() { return $this->backend_request('public/sustainable-development/freshness'); }
    public function rest_public_sustainable_development_schema_validation() { return $this->backend_request('public/sustainable-development/schema-validation'); }
    public function rest_public_sustainable_development_cache_status() { return $this->backend_request('public/sustainable-development/cache'); }

    public function rest_public_planetary_boundaries_observatory() { return $this->backend_request('public/planetary-boundaries'); }
    public function rest_public_planetary_boundary(WP_REST_Request $request) {
        $id = sanitize_title((string) $request->get_param('id'));
        return $this->backend_request('public/planetary-boundaries/' . rawurlencode($id));
    }
    public function rest_public_planetary_boundary_trend(WP_REST_Request $request) {
        $id = sanitize_title((string) $request->get_param('id'));
        return $this->backend_request('public/planetary-boundaries/' . rawurlencode($id) . '/trend');
    }
    public function rest_public_planetary_boundary_sources(WP_REST_Request $request) {
        $id = sanitize_title((string) $request->get_param('id'));
        return $this->backend_request('public/planetary-boundaries/sources' . ($id ? '?boundary_id=' . rawurlencode($id) : ''));
    }
    public function rest_public_planetary_boundary_methodology() { return $this->backend_request('public/planetary-boundaries/methodology'); }
    public function rest_public_planetary_boundary_export() { return $this->backend_request('public/planetary-boundaries/export'); }
    public function rest_public_humanitarian_intelligence() { return $this->backend_request('public/humanitarian-intelligence'); }
    public function rest_public_humanitarian_crisis_map() { return $this->backend_request('public/humanitarian-intelligence/crisis-map'); }
    public function rest_public_humanitarian_reports() { return $this->backend_request('public/humanitarian-intelligence/reports'); }
    public function rest_public_displacement_context() { return $this->backend_request('public/humanitarian-intelligence/displacement'); }
    public function rest_public_humanitarian_sources() { return $this->backend_request('public/humanitarian-intelligence/sources'); }
    public function rest_public_humanitarian_methodology() { return $this->backend_request('public/humanitarian-intelligence/methodology'); }
    public function rest_public_humanitarian_export() { return $this->backend_request('public/humanitarian-intelligence/export'); }
    public function rest_public_human_development() { return $this->backend_request('public/human-development'); }
    public function rest_public_human_development_sources() { return $this->backend_request('public/human-development/sources'); }
    public function rest_public_human_development_domain(WP_REST_Request $request) { $id = sanitize_title($request->get_param('id')); return $this->backend_request('public/human-development/domains/' . rawurlencode($id ?: 'poverty')); }
    public function rest_public_human_development_country_profile(WP_REST_Request $request) { $country = sanitize_text_field($request->get_param('country')); return $this->backend_request('public/human-development/country-profile' . ($country ? '?country=' . rawurlencode($country) : '')); }
    public function rest_public_human_development_inequalities() { return $this->backend_request('public/human-development/inequalities'); }
    public function rest_public_human_development_methodology() { return $this->backend_request('public/human-development/methodology'); }
    public function rest_public_human_development_export() { return $this->backend_request('public/human-development/export'); }
    public function rest_public_international_law() { return $this->backend_request('public/international-law'); }
    public function rest_public_international_law_sources() { return $this->backend_request('public/international-law/sources'); }
    public function rest_public_international_law_sanctions() { return $this->backend_request('public/international-law/sanctions'); }
    public function rest_public_international_law_events(WP_REST_Request $request) { $params = []; $event_type = sanitize_text_field($request->get_param('event_type')); $jurisdiction = sanitize_text_field($request->get_param('jurisdiction')); if ($event_type) { $params['event_type'] = $event_type; } if ($jurisdiction) { $params['jurisdiction'] = $jurisdiction; } return $this->backend_request('public/international-law/events' . ($params ? '?' . http_build_query($params) : '')); }
    public function rest_public_international_law_monitor(WP_REST_Request $request) { $id = sanitize_title($request->get_param('id')); return $this->backend_request('public/international-law/monitors/' . rawurlencode($id ?: 'sanctions')); }
    public function rest_public_international_law_methodology() { return $this->backend_request('public/international-law/methodology'); }
    public function rest_public_international_law_export() { return $this->backend_request('public/international-law/export'); }
    public function rest_public_human_security() { return $this->backend_request('public/human-security'); }
    public function rest_public_human_security_sources() { return $this->backend_request('public/human-security/sources'); }
    public function rest_public_human_security_events(WP_REST_Request $request) { $params = []; $record_type = sanitize_text_field($request->get_param('record_type')); $country = sanitize_text_field($request->get_param('country')); if ($record_type) { $params['record_type'] = $record_type; } if ($country) { $params['country'] = $country; } return $this->backend_request('public/human-security/events' . ($params ? '?' . http_build_query($params) : '')); }
    public function rest_public_human_security_monitor(WP_REST_Request $request) { $id = sanitize_title($request->get_param('id')); return $this->backend_request('public/human-security/monitors/' . rawurlencode($id ?: 'conflict-events')); }
    public function rest_public_human_security_displacement() { return $this->backend_request('public/human-security/displacement'); }
    public function rest_public_human_security_modeled_risk() { return $this->backend_request('public/human-security/modeled-risk'); }
    public function rest_public_human_security_methodology() { return $this->backend_request('public/human-security/methodology'); }
    public function rest_public_human_security_export() { return $this->backend_request('public/human-security/export'); }
    public function rest_public_geospatial() { return $this->backend_request('public/geospatial'); }
    public function rest_public_geospatial_layers() { return $this->backend_request('public/geospatial/layers'); }
    public function rest_public_geospatial_events(WP_REST_Request $request) { $category = sanitize_text_field($request->get_param('category')) ?: 'all'; return $this->backend_request('public/geospatial/events?category=' . rawurlencode($category)); }
    public function rest_public_geospatial_heatmap() { return $this->backend_request('public/geospatial/heatmap'); }
    public function rest_public_geospatial_satellite(WP_REST_Request $request) { $date = sanitize_text_field($request->get_param('date')); return $this->backend_request('public/geospatial/satellite' . ($date ? '?date=' . rawurlencode($date) : '')); }
    public function rest_public_geospatial_accessibility() { return $this->backend_request('public/geospatial/accessibility'); }

    public function rest_public_cross_domain_dashboards() { return $this->backend_request('public/dashboard-studio'); }
    public function rest_public_cross_domain_dashboard_manifest() { return $this->backend_request('public/dashboard-studio/manifest'); }
    public function rest_public_dashboard_launch_manifest() { return $this->backend_request('public/dashboard-studio/launch-manifest'); }
    public function rest_public_dashboard_launch_readiness() { return $this->backend_request('public/dashboard-studio/launch-readiness'); }
    public function rest_public_dashboard_studio_navigation() { return $this->backend_request('public/dashboard-studio/navigation'); }
    private function cross_domain_fallback($type, $country = 'KEN', $compare = 'GHA', $dashboard_id = 'climate-human-vulnerability') {
        $country = strtoupper($country ?: 'KEN');
        $compare = strtoupper($compare ?: 'GHA');
        $domains = ['sustainable-development','planetary-boundaries','human-development','humanitarian-intelligence','human-security','international-law'];
        $labels = [
            'sustainable-development'=>'Sustainable development','planetary-boundaries'=>'Environmental pressure','human-development'=>'Human development',
            'humanitarian-intelligence'=>'Humanitarian conditions','human-security'=>'Human security','international-law'=>'International law'
        ];
        $items = array_map(function($domain) use ($labels, $country) {
            return ['domain'=>$domain,'label'=>$labels[$domain] ?? $domain,'description'=>'Source registry and methodology context remain available while the live connector is unavailable.','geography'=>$country,'source_count'=>0,'sources'=>[],'data_state'=>'wordpress-local-fallback','freshness'=>'unavailable','value_status'=>'No value displayed because a validated live record was not returned.'];
        }, $domains);
        $base = ['ok'=>true,'version'=>self::VERSION,'origin_state'=>'wordpress-local-fallback','data_state'=>'wordpress-local-fallback','generated_at'=>gmdate('c'),'notes'=>['This is a transparent local fallback, not live backend data.','No precise values are invented or silently imputed.']];
        if ($type === 'dashboard') return array_merge($base,['dashboard_id'=>$dashboard_id,'title'=>'Public Intelligence Dashboard','summary'=>'Live dashboard data is temporarily unavailable. Source and methodology context remains visible.','evidence_items'=>array_slice($items,1,4),'source_summary'=>['registered_sources'=>0,'domains'=>4,'freshness'=>'unavailable','live_values_policy'=>'Only validated connector values are displayed.']]);
        if ($type === 'country') return array_merge($base,['country_code'=>$country,'country_name'=>$country,'profile_status'=>'wordpress-local-fallback','summary'=>'Live country evidence is temporarily unavailable.','evidence_items'=>$items,'source_summary'=>['registered_sources'=>0,'domains'=>6,'freshness'=>'unavailable','missing_data_policy'=>'Missing values remain explicit.'],'governance'=>['Country profiles are not rankings.','Missing data is not silently imputed.']]);
        $rows = array_map(function($dimension) use ($country,$compare) { return ['dimension'=>$dimension,'left'=>['country'=>$country,'value'=>null,'data_state'=>'unavailable'],'right'=>['country'=>$compare,'value'=>null,'data_state'=>'unavailable'],'display_note'=>'No validated connector value was returned.']; }, ['human-development','environmental-pressure','disaster-exposure','conflict-displacement','international-law-context','source-coverage']);
        return array_merge($base,['countries'=>[$country,$compare],'status'=>'wordpress-local-fallback','summary'=>'Live comparison data is temporarily unavailable.','comparison_rows'=>$rows,'normalization_rule'=>'Display original units and definitions; do not combine unlike indicators into one score.']);
    }

    public function rest_public_dashboard_rendering_diagnostics() { return $this->backend_request('public/dashboard-studio/rendering-diagnostics'); }

    public function rest_public_cross_domain_dashboard(WP_REST_Request $request) { $id = sanitize_title($request->get_param('id')) ?: 'climate-human-vulnerability'; $view = sanitize_key($request->get_param('view')) ?: 'data'; $country = strtoupper(sanitize_text_field($request->get_param('country'))); $region = sanitize_text_field($request->get_param('region')); $start = sanitize_text_field($request->get_param('start')); $end = sanitize_text_field($request->get_param('end')); $compare = strtoupper(sanitize_text_field($request->get_param('compare'))); $suffix = $view === 'brief' ? '/brief' : '/data'; $params = array_filter(['country'=>$country,'region'=>$region,'start'=>$start,'end'=>$end,'compare'=>$compare]); $result = $this->backend_request('public/dashboard-studio/' . rawurlencode($id) . $suffix . ($params ? '?' . http_build_query($params) : '')); return is_wp_error($result) ? $this->cross_domain_fallback('dashboard', $country, $compare, $id) : $result; }
    public function rest_public_cross_domain_dashboard_sources(WP_REST_Request $request) { $id = sanitize_title($request->get_param('id')); return $this->backend_request('public/dashboard-studio/' . rawurlencode($id ?: 'climate-human-vulnerability') . '/sources'); }
    public function rest_public_cross_domain_dashboard_export(WP_REST_Request $request) { $id = sanitize_title($request->get_param('id')); $country = sanitize_text_field($request->get_param('country')); return $this->backend_request('public/dashboard-studio/' . rawurlencode($id ?: 'climate-human-vulnerability') . '/export' . ($country ? '?country=' . rawurlencode($country) : '')); }
    public function rest_public_country_intelligence(WP_REST_Request $request) { $country = strtoupper(sanitize_text_field($request->get_param('country'))) ?: 'KEN'; $result = $this->backend_request('public/country-intelligence/' . rawurlencode($country)); return is_wp_error($result) ? $this->cross_domain_fallback('country', $country) : $result; }
    public function rest_public_cross_domain_comparison(WP_REST_Request $request) { $country = strtoupper(sanitize_text_field($request->get_param('country'))) ?: 'KEN'; $compare = strtoupper(sanitize_text_field($request->get_param('compare'))) ?: 'GHA'; $result = $this->backend_request('public/cross-domain-comparison?' . http_build_query(['country'=>$country,'compare'=>$compare])); return is_wp_error($result) ? $this->cross_domain_fallback('comparison', $country, $compare) : $result; }

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


    public function rest_public_page_builder(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_page_builder_shortcodes(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder/shortcodes');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_page_builder_readiness(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder/readiness');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_page_builder_visual_qa(WP_REST_Request $request) {
        $result = $this->backend_request('public/page-builder/visual-qa');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
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


    public function rest_public_dashboard_directory(WP_REST_Request $request) {
        $result = $this->backend_request('public/dashboard-studio');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_topic_dashboard(WP_REST_Request $request) {
        $topic = sanitize_key($request->get_param('topic'));
        $allowed = ['climate-energy', 'environmental-monitoring', 'biodiversity-land-use', 'knowledge-system', 'search-discovery'];
        if (!in_array($topic, $allowed, true)) {
            return new WP_REST_Response(['ok' => false, 'message' => 'Unknown public topic dashboard.'], 400);
        }
        $result = $this->backend_request('public/dashboards/' . $topic);
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_source_methodology(WP_REST_Request $request) {
        $result = $this->backend_request('public/source-methodology');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_dashboard_navigation(WP_REST_Request $request) {
        $current = sanitize_key($request->get_param('current'));
        $endpoint = 'public/navigation' . ($current ? '?current=' . rawurlencode($current) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_topic_page_templates(WP_REST_Request $request) {
        $slug = sanitize_key($request->get_param('slug'));
        $endpoint = 'public/page-templates' . ($slug ? '?slug=' . rawurlencode($slug) : '');
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_topic_page_visual_qa(WP_REST_Request $request) {
        $result = $this->backend_request('public/topic-page-visual-qa');
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    private function public_source_endpoint_map($key) {
        $map = [
            'api_sources' => 'public/sources',
            'source_health' => 'public/sources/health',
            'development_indicators' => 'public/sources/development-indicators',
            'research_metadata' => 'public/sources/research-metadata',
            'publication_metadata' => 'public/sources/publications',
            'repository_intelligence' => 'public/sources/repositories',
            'indicator_overview' => 'public/indicators/overview',
            'sustainability_indicators' => 'public/indicators/sustainability',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/sources';
    }

    private function rest_public_source_panel($key) {
        $result = $this->backend_request($this->public_source_endpoint_map($key));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_api_sources(WP_REST_Request $request) { return $this->rest_public_source_panel('api_sources'); }
    public function rest_public_source_health(WP_REST_Request $request) { return $this->rest_public_source_panel('source_health'); }
    public function rest_public_development_indicators(WP_REST_Request $request) { return $this->rest_public_source_panel('development_indicators'); }
    public function rest_public_research_metadata(WP_REST_Request $request) { return $this->rest_public_source_panel('research_metadata'); }
    public function rest_public_publication_metadata(WP_REST_Request $request) { return $this->rest_public_source_panel('publication_metadata'); }
    public function rest_public_repository_intelligence(WP_REST_Request $request) { return $this->rest_public_source_panel('repository_intelligence'); }
    public function rest_public_indicator_overview(WP_REST_Request $request) { return $this->rest_public_source_panel('indicator_overview'); }
    public function rest_public_sustainability_indicators(WP_REST_Request $request) { return $this->rest_public_source_panel('sustainability_indicators'); }

    private function public_connector_endpoint_map($key) {
        $map = [
            'connector_status' => 'public/connectors/status',
            'cache_status' => 'public/connectors/cache',
            'source_freshness' => 'public/connectors/freshness',
            'connector_reliability' => 'public/connectors/reliability',
            'connector_status_polish' => 'public/connectors/status-polish',
            'world_bank' => 'public/connectors/world-bank',
            'openalex' => 'public/connectors/openalex',
            'crossref' => 'public/connectors/crossref',
            'github' => 'public/connectors/github',
            'environmental' => 'public/connectors/environmental',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/connectors/status';
    }

    private function rest_public_connector_panel($key) {
        $result = $this->backend_request($this->public_connector_endpoint_map($key));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    public function rest_public_connector_status(WP_REST_Request $request) { return $this->rest_public_connector_panel('connector_status'); }
    public function rest_public_cache_status(WP_REST_Request $request) { return $this->rest_public_connector_panel('cache_status'); }
    public function rest_public_source_freshness(WP_REST_Request $request) { return $this->rest_public_connector_panel('source_freshness'); }
    public function rest_public_connector_reliability(WP_REST_Request $request) { return $this->rest_public_connector_panel('connector_reliability'); }
    public function rest_public_connector_status_polish(WP_REST_Request $request) { return $this->rest_public_connector_panel('connector_status_polish'); }

    public function rest_public_connector_detail(WP_REST_Request $request) {
        $slug = sanitize_key($request->get_param('slug'));
        $allowed = ['world-bank', 'openalex', 'crossref', 'github', 'environmental'];
        if (!in_array($slug, $allowed, true)) {
            return new WP_REST_Response(['ok' => false, 'message' => 'Unknown public connector slug.'], 400);
        }
        return $this->rest_public_connector_panel(str_replace('-', '_', $slug));
    }


    private function public_indicator_chart_endpoint_map($key) {
        $map = [
            'directory' => 'public/indicator-dashboards',
            'sustainability' => 'public/indicator-dashboards/sustainability',
            'development' => 'public/indicator-dashboards/development',
            'source_health' => 'public/indicator-dashboards/source-health',
            'research' => 'public/indicator-dashboards/research',
            'repository' => 'public/indicator-dashboards/repository',
            'gallery' => 'public/indicator-dashboards/charts',
            'visual_qa' => 'public/indicator-dashboards/visual-qa',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/indicator-dashboards';
    }

    public function rest_public_indicator_chart_panel(WP_REST_Request $request) {
        $panel = sanitize_key($request->get_param('panel'));
        $result = $this->backend_request($this->public_indicator_chart_endpoint_map(str_replace('-', '_', $panel)));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }


    private function public_source_aware_brief_endpoint_map($key) {
        $map = [
            'directory' => 'public/source-aware-briefs',
            'site_intelligence' => 'public/source-aware-briefs/site-intelligence',
            'indicator' => 'public/source-aware-briefs/indicator',
            'source_health' => 'public/source-aware-briefs/source-health',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/source-aware-briefs';
    }

    public function rest_public_source_aware_brief_panel(WP_REST_Request $request) {
        $panel = sanitize_key($request->get_param('panel'));
        $result = $this->backend_request($this->public_source_aware_brief_endpoint_map(str_replace('-', '_', $panel)));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
        }
        return rest_ensure_response($result);
    }

    private function public_dashboard_export_endpoint_map($key) {
        $map = [
            'manifest' => 'public/dashboard-exports/manifest',
            'site_intelligence' => 'public/dashboard-exports/site-intelligence',
            'indicator' => 'public/dashboard-exports/indicator',
            'source_health' => 'public/dashboard-exports/source-health',
            'visual_qa' => 'public/dashboard-exports/visual-qa',
        ];
        return isset($map[$key]) ? $map[$key] : 'public/dashboard-exports/manifest';
    }

    public function rest_public_dashboard_export_panel(WP_REST_Request $request) {
        $panel = sanitize_key($request->get_param('panel'));
        $result = $this->backend_request($this->public_dashboard_export_endpoint_map(str_replace('-', '_', $panel)));
        if (is_wp_error($result)) {
            return new WP_REST_Response(['ok' => false, 'message' => $result->get_error_message()], 502);
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


    private function report_query_args(WP_REST_Request $request, $keys = []) {
        $query = [];
        foreach ($keys as $key) {
            $value = $request->get_param($key);
            if (!empty($value)) {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    private function proxy_report($endpoint, WP_REST_Request $request, $keys = []) {
        $query = $this->report_query_args($request, array_merge(['start_date', 'end_date', 'format'], $keys));
        $result = $this->backend_request($endpoint . (!empty($query) ? '?' . http_build_query($query) : ''));
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_report_site_intelligence(WP_REST_Request $request) {
        return $this->proxy_report('reports/site-intelligence', $request);
    }

    public function rest_report_search_intelligence(WP_REST_Request $request) {
        return $this->proxy_report('reports/search-intelligence', $request);
    }

    public function rest_report_content_strategy(WP_REST_Request $request) {
        return $this->proxy_report('reports/content-strategy', $request, ['prior_start_date', 'prior_end_date', 'limit']);
    }

    public function rest_report_external_sources(WP_REST_Request $request) {
        return $this->proxy_report('reports/external-sources', $request);
    }

    public function rest_report_climate_energy(WP_REST_Request $request) {
        return $this->proxy_report('reports/climate-energy', $request, ['latitude', 'longitude', 'country', 'start', 'end', 'year', 'live']);
    }

    public function rest_report_indexing(WP_REST_Request $request) {
        return $this->proxy_report('reports/indexing', $request);
    }

    public function rest_report_export(WP_REST_Request $request) {
        return $this->proxy_report('reports/export', $request, ['report']);
    }

    public function rest_reports_summary(WP_REST_Request $request) {
        $result = $this->backend_request('intelligence/reports');
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }



    private function local_public_dashboard_ai_brief() {
        return [
            'ok' => true,
            'brief_id' => 'public-dashboard-ai-brief',
            'title' => 'AI-Assisted Public Dashboard Brief',
            'summary' => 'Interpret public-safe dashboard status, methodology notes, knowledge overview, and public release readiness.',
            'generated_at' => gmdate('c'),
            'mode' => 'public',
            'provider' => 'deterministic-local',
            'model' => 'wordpress-fallback-v1.6.0',
            'source_report' => [
                'report_id' => 'public-dashboard',
                'title' => 'Public Dashboard Readiness Report',
                'source' => ['dashboard' => 'wordpress-local-fallback', 'mode' => 'public-safe', 'live_analytics' => false],
                'date_range' => [],
            ],
            'executive_summary' => 'The Sustainable Catalyst public dashboard layer is suitable for reviewed public presentation when it uses sanitized, source-labeled summaries, methodology notes, and public-safe snapshots rather than raw analytics or live operational diagnostics.',
            'key_findings' => [
                'Public dashboard modules should remain aggregated, reviewed, and source-labeled.',
                'Raw GA4 analytics, conversion diagnostics, report queues, and operational notes should remain private.',
                'Public pages should use fast snapshots by default and reserve live connector calls for private testing.',
            ],
            'recommended_actions' => [
                'Use the public landing, public knowledge overview, climate/energy summary, and methodology shortcodes on public pages.',
                'Keep the Public Dashboard Brief deterministic unless directly testing the backend route.',
                'Review all public copy before promoting the dashboard as a flagship platform asset.',
                'Pair public summaries with clear educational and analytical boundaries.',
            ],
            'content_opportunities' => [
                'Create a public Site Intelligence landing page that explains the knowledge-system layer without exposing private analytics.',
                'Use the public dashboard as portfolio evidence for open infrastructure, analytics, and responsible sustainability tooling.',
                'Turn reviewed public dashboard findings into LinkedIn or Substack updates only after manual review.',
            ],
            'risk_notes' => [
                'Public dashboards should not expose raw analytics, private recommendations, API configuration, or backend diagnostic details.',
                'External-source summaries can be delayed, cached, or unavailable; public copy should describe source and freshness limits.',
                'This local fallback exists so the page remains stable even when Render, Bluehost, Cloudflare, or an AI provider is unavailable.',
            ],
            'public_safe_summary' => 'Public Site Intelligence can be presented as a reviewed, source-labeled dashboard framework for Sustainable Catalyst. It should emphasize methodology, knowledge architecture, public data context, and educational boundaries while keeping raw analytics and operational diagnostics private.',
            'private_notes' => [],
            'confidence' => [
                'level' => 'medium',
                'basis' => 'Generated from the v0.9.0 WordPress local fallback to avoid gateway-dependent public rendering.',
            ],
            'methodology' => [
                'summary' => 'v0.9.0 renders the public-dashboard brief locally by default to prevent gateway errors from affecting dashboard pages.',
                'privacy_note' => 'No raw analytics, external API calls, API tokens, or private report payloads are used in this fallback.',
            ],
        ];
    }

    private function ai_brief_query_args(WP_REST_Request $request, $keys = []) {
        $query = [];
        foreach ($keys as $key) {
            $value = $request->get_param($key);
            if ($value !== null && $value !== '') {
                $query[$key] = sanitize_text_field($value);
            }
        }
        return $query;
    }

    private function proxy_ai_brief($endpoint, WP_REST_Request $request, $keys = []) {
        $query = $this->ai_brief_query_args($request, array_merge(['start_date', 'end_date', 'prior_start_date', 'prior_end_date', 'limit', 'mode', 'use_ai', 'format'], $keys));
        $result = $this->backend_request($endpoint . (!empty($query) ? '?' . http_build_query($query) : ''));
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_ai_status(WP_REST_Request $request) {
        $result = $this->backend_request('ai/status');
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_ai_site_intelligence_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/site-intelligence', $request);
    }

    public function rest_ai_search_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/search', $request);
    }

    public function rest_ai_publishing_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/publishing', $request);
    }

    public function rest_ai_external_sources_brief(WP_REST_Request $request) {
        return $this->proxy_ai_brief('ai/briefs/external-sources', $request);
    }

    public function rest_ai_public_dashboard_brief(WP_REST_Request $request) {
        $live = $request->get_param('live');
        if ($live !== 'true' && $live !== '1') {
            return rest_ensure_response($this->local_public_dashboard_ai_brief());
        }
        $result = $this->proxy_ai_brief('ai/briefs/public-dashboard', $request);
        if (is_wp_error($result)) {
            return rest_ensure_response($this->local_public_dashboard_ai_brief());
        }
        return $result;
    }

    public function rest_ai_briefs_summary(WP_REST_Request $request) {
        $result = $this->backend_request('intelligence/ai-briefs');
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    private function proxy_admin_control($endpoint) {
        $result = $this->backend_request($endpoint);
        if (is_wp_error($result)) { return $result; }
        return rest_ensure_response($result);
    }

    public function rest_admin_overview(WP_REST_Request $request) {
        return $this->proxy_admin_control('intelligence/admin');
    }

    public function rest_admin_registry(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/registry');
    }

    public function rest_admin_sources(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/sources');
    }

    public function rest_admin_modules(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/modules');
    }

    public function rest_admin_shortcodes(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/shortcodes');
    }

    public function rest_admin_diagnostics(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/diagnostics');
    }

    public function rest_admin_visibility(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/visibility');
    }

    public function rest_admin_source_control(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/source-control');
    }


    public function rest_admin_status(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/status');
    }

    public function rest_admin_connection_check(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/connection-check');
    }

    public function rest_admin_public_readiness_check(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/public-readiness-check');
    }

    public function rest_admin_diagnostic_summary(WP_REST_Request $request) {
        return $this->proxy_admin_control('admin/diagnostic-summary');
    }

    public function rest_release_status(WP_REST_Request $request) {
        return $this->proxy_admin_control('release/status');
    }

    public function rest_release_smoke_test(WP_REST_Request $request) {
        return $this->proxy_admin_control('release/smoke-test');
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
            <p>Connect Sustainable Catalyst to the Site Intelligence backend, review deployment health, and manage private/public dashboard placement.</p>
            <div class="scsi-admin-panel-grid">
                <div class="scsi-admin-panel"><h2>Connection</h2><p>Confirm the Render backend URL, API token, and current deployed version.</p><p><a class="button" href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/admin-status')); ?>" target="_blank" rel="noopener">Open Admin Status</a></p></div>
                <div class="scsi-admin-panel"><h2>Diagnostics</h2><p>Use the one-click diagnostic summary after each deploy.</p><p><a class="button" href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/admin-diagnostic-summary')); ?>" target="_blank" rel="noopener">Open Diagnostic Summary</a></p></div>
                <div class="scsi-admin-panel"><h2>Public / Private</h2><p>Keep raw analytics, reports, AI drafts, and admin diagnostics on private pages.</p><p><a class="button" href="<?php echo esc_url(rest_url(self::REST_NAMESPACE . '/admin-public-readiness-check')); ?>" target="_blank" rel="noopener">Open Public Readiness</a></p></div>
            </div>
            <?php
            $version_status = get_option(self::BUILD_INFO_STATUS_OPTION, []);
            if (!is_array($version_status) || empty($version_status)) {
                $version_status = $this->verify_backend_version(false);
            }
            $version_state = sanitize_key((string) ($version_status['state'] ?? 'unknown'));
            $version_backend = sanitize_text_field((string) ($version_status['backend_version'] ?? ''));
            $version_checked = sanitize_text_field((string) ($version_status['checked_at'] ?? 'Never'));
            $version_http = (int) ($version_status['http_status'] ?? 0);
            $version_url = sanitize_text_field((string) ($version_status['backend_url'] ?? ($options['backend_url'] ?? '')));
            ?>
            <div class="notice inline <?php echo $version_state === 'match' ? 'notice-success' : ($version_state === 'mismatch' ? 'notice-warning' : 'notice-info'); ?>">
                <p><strong>Backend version verification</strong></p>
                <p>
                    State: <code><?php echo esc_html($version_state); ?></code> ·
                    Plugin: <code><?php echo esc_html(self::VERSION); ?></code> ·
                    Backend: <code><?php echo esc_html($version_backend !== '' ? $version_backend : 'unknown'); ?></code> ·
                    HTTP: <code><?php echo esc_html((string) $version_http); ?></code>
                </p>
                <p>Checked URL: <code><?php echo esc_html($version_url !== '' ? $version_url : 'not configured'); ?></code><br />Last verification: <code><?php echo esc_html($version_checked); ?></code></p>
                <p><a class="button button-secondary" href="<?php echo esc_url($this->backend_version_refresh_url()); ?>">Refresh backend version</a></p>
            </div>
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
            <h2>Public Source Pages</h2>
            <p><code>[sc_public_source_page_directory]</code></p>
            <p><code>[sc_public_source_navigation]</code></p>
            <p><code>[sc_public_source_page_templates]</code></p>
            <p><code>[sc_public_source_page_visual_qa]</code></p>
            <h2>Public Connector Status</h2>
            <p><code>[sc_public_connector_status]</code></p>
            <p><code>[sc_public_cache_status]</code></p>
            <p><code>[sc_public_source_freshness]</code></p>
            <p><code>[sc_public_world_bank_connector]</code></p>
            <p><code>[sc_public_openalex_connector]</code></p>
            <p><code>[sc_public_crossref_connector]</code></p>
            <p><code>[sc_public_github_connector]</code></p>
            <p><code>[sc_public_environmental_connectors]</code></p>
            <h2>AI-Assisted Briefs</h2>
            <p><code>[sc_ai_brief_status]</code></p>
            <p><code>[sc_ai_site_intelligence_brief]</code></p>
            <p><code>[sc_ai_search_brief]</code></p>
            <p><code>[sc_ai_publishing_brief]</code></p>
            <p><code>[sc_ai_external_sources_brief]</code></p>
            <p><code>[sc_ai_public_dashboard_brief]</code></p>
            <h2>Admin Control Plane</h2>
            <p><code>[sc_site_intelligence_admin_overview]</code></p>
            <p><code>[sc_site_intelligence_shortcode_catalog]</code></p>
            <p><code>[sc_site_intelligence_module_status]</code></p>
            <p><code>[sc_site_intelligence_diagnostic_summary]</code></p>
            <p><code>[sc_site_intelligence_connection_check]</code></p>
            <p><code>[sc_site_intelligence_release_status]</code></p>
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



    public function public_flagship_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'title' => 'Sustainable Catalyst Site Intelligence',
            'subtitle' => 'A public-safe dashboard for knowledge architecture, public source signals, methodology, and platform transparency.',
            'show_cta' => 'true',
        ], $atts, 'sc_site_intelligence_public_flagship');
        ob_start();
        ?>
        <section class="scsi-public-flagship" data-scsi-public-flagship>
            <div class="scsi-flagship-hero">
                <p class="scsi-eyebrow">Sustainable Catalyst Site Intelligence</p>
                <h2><?php echo esc_html($atts['title']); ?></h2>
                <p class="scsi-flagship-lede"><?php echo esc_html($atts['subtitle']); ?></p>
                <p class="scsi-public-boundary">Educational and informational only. This page does not provide legal, financial, medical, engineering, climate-risk, ESG, compliance, assurance, or investment advice.</p>
                <?php if ($atts['show_cta'] !== 'false') : ?>
                <div class="scsi-public-cta-row scsi-flagship-cta-row">
                    <a class="scsi-public-cta" href="https://sustainablecatalyst.com/research-library/" data-scsi-event="sc_library_nav">Explore the Research Library</a>
                    <a class="scsi-public-cta" href="https://sustainablecatalyst.com/workbench/" data-scsi-event="sc_workbench_open">Open the Workbench</a>
                    <a class="scsi-public-cta" href="https://github.com/Content-Catalyst-LLC" target="_blank" rel="noopener" data-scsi-event="sc_repository_click">View the GitHub Repositories</a>
                </div>
                <?php endif; ?>
            </div>
            <div class="scsi-flagship-stack">
                <?php
                echo $this->public_landing_shortcode([]);
                echo $this->public_site_intelligence_shortcode([]);
                echo $this->public_knowledge_overview_shortcode([]);
                echo $this->public_climate_energy_summary_shortcode([]);
                echo $this->public_methodology_shortcode([]);
                ?>
            </div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_page_builder_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-page-builder" data-scsi-public-page-builder>
            <p class="scsi-eyebrow">Public Dashboard Page Builder</p>
            <h2>Public Flagship Dashboard Page Builder</h2>
            <p class="scsi-muted">Loading public-safe page presets, release checklist, and placement guidance…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_shortcode_bundle_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-shortcode-bundle" data-scsi-public-shortcode-bundle>
            <p class="scsi-eyebrow">Public Dashboard Shortcode Bundles</p>
            <h2>Copy-Ready Public Dashboard Bundles</h2>
            <p class="scsi-muted">Loading public-safe shortcode bundles…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_visual_qa_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-visual-qa" data-scsi-public-visual-qa>
            <p class="scsi-eyebrow">Public Dashboard Visual QA</p>
            <h2>Visual QA and Copy Polish</h2>
            <p class="scsi-muted">Loading public dashboard visual QA, copy guidance, and launch notes…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
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



    public function public_dashboard_navigation_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'current' => '',
            'title' => 'Site Intelligence Public Dashboards',
        ], $atts, 'sc_public_dashboard_navigation');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-dashboard-navigation" data-scsi-public-dashboard-navigation data-current="<?php echo esc_attr(sanitize_key($atts['current'])); ?>">
            <p class="scsi-eyebrow">Dashboard Navigation</p>
            <h2><?php echo esc_html($atts['title']); ?></h2>
            <p class="scsi-muted">Loading public dashboard navigation…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_topic_page_templates_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $atts = shortcode_atts([
            'slug' => '',
            'title' => 'Public Topic Page Templates',
        ], $atts, 'sc_public_topic_page_templates');
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-page-templates" data-scsi-public-topic-page-templates data-slug="<?php echo esc_attr(sanitize_key($atts['slug'])); ?>">
            <p class="scsi-eyebrow">Page Templates</p>
            <h2><?php echo esc_html($atts['title']); ?></h2>
            <p class="scsi-muted">Loading public topic page templates…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_topic_page_visual_qa_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-page-visual-qa" data-scsi-public-topic-page-visual-qa>
            <p class="scsi-eyebrow">Topic Page QA</p>
            <h2>Site Intelligence Public Topic Page QA</h2>
            <p class="scsi-muted">Loading public topic page QA…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_dashboard_directory_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-directory" data-scsi-public-dashboard-directory>
            <p class="scsi-eyebrow">Public Topic Dashboards</p>
            <h2>Public Dashboard Directory</h2>
            <p class="scsi-muted">Loading public-safe topic dashboard directory…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function topic_from_shortcode_tag($tag) {
        $map = [
            'sc_public_climate_energy_dashboard' => 'climate-energy',
            'sc_public_environmental_monitoring_dashboard' => 'environmental-monitoring',
            'sc_public_biodiversity_land_use_dashboard' => 'biodiversity-land-use',
            'sc_public_knowledge_system_dashboard' => 'knowledge-system',
            'sc_public_search_discovery_dashboard' => 'search-discovery',
        ];
        return isset($map[$tag]) ? $map[$tag] : 'knowledge-system';
    }

    public function public_topic_dashboard_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $topic = $this->topic_from_shortcode_tag($tag);
        $titles = [
            'climate-energy' => 'Climate + Energy Public Dashboard',
            'environmental-monitoring' => 'Environmental Monitoring Public Dashboard',
            'biodiversity-land-use' => 'Biodiversity + Land Use Public Dashboard',
            'knowledge-system' => 'Knowledge-System Public Dashboard',
            'search-discovery' => 'Search + Discovery Public Dashboard',
        ];
        ob_start();
        ?>
        <section class="scsi-card scsi-public-topic-dashboard" data-scsi-public-topic-dashboard data-topic="<?php echo esc_attr($topic); ?>">
            <p class="scsi-eyebrow">Public Topic Dashboard</p>
            <h2><?php echo esc_html($titles[$topic]); ?></h2>
            <p class="scsi-muted">Loading public-safe topic dashboard…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_source_methodology_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-source-methodology" data-scsi-public-source-methodology>
            <p class="scsi-eyebrow">Public Source Methodology</p>
            <h2>Source Notes, Fallbacks, and Public Boundaries</h2>
            <p class="scsi-muted">Loading public source methodology…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function public_api_sources_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        ob_start();
        ?>
        <section class="scsi-card scsi-public-api-sources" data-scsi-public-source-panel data-source-panel="api-sources">
            <p class="scsi-eyebrow">Public API Sources</p>
            <h2>Public API Source Expansion</h2>
            <p class="scsi-muted">Loading public API source families…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function public_source_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_source_health' => ['source-health', 'Public Source Health', 'Source-health labels for live, cached, fallback, and planned source families.'],
            'sc_public_development_indicators' => ['development-indicators', 'Development Indicators', 'World Bank, OECD, and UN/SDG indicator context for public dashboards.'],
            'sc_public_research_metadata' => ['research-metadata', 'Research Metadata', 'OpenAlex and Crossref research metadata context for public source discovery.'],
            'sc_public_publication_metadata' => ['publication-metadata', 'Publication Metadata', 'Publication and DOI metadata context for public bibliography/source panels.'],
            'sc_public_repository_intelligence' => ['repository-intelligence', 'Repository Intelligence', 'GitHub repository intelligence for public code-infrastructure visibility.'],
            'sc_public_indicator_overview' => ['indicator-overview', 'Indicator Overview', 'Public indicator overview across live, cached, fallback, and planned source families.'],
            'sc_public_sustainability_indicators' => ['sustainability-indicators', 'Sustainability Indicators', 'Sustainability indicator context across environment, development, research, and repository layers.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['source-health', 'Public Source Health', 'Loading public source panel…'];
    }

    public function public_source_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_source_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-source-panel" data-scsi-public-source-panel data-source-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Source Layer</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function public_connector_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_connector_status' => ['connector-status', 'Public Connector Status', 'Live, cached, fallback, and planned connector readiness for public source panels.'],
            'sc_public_cache_status' => ['cache-status', 'Public Cache Status', 'Cache TTL, stale-safe display, and public source refresh policy.'],
            'sc_public_source_freshness' => ['source-freshness', 'Public Source Freshness', 'Freshness labels for public source families and connector panels.'],
            'sc_public_connector_reliability' => ['connector-reliability', 'Connector Reliability Summary', 'Public display reliability, recovery guidance, and degraded/fallback-safe source labels.'],
            'sc_public_connector_status_polish' => ['connector-status-polish', 'Public Source Status Polish', 'Display guidance for public connector panels, status cards, reliability labels, and fallback language.'],
            'sc_public_world_bank_connector' => ['world-bank', 'World Bank Connector', 'Development indicator source status, cache policy, and fallback notes.'],
            'sc_public_openalex_connector' => ['openalex', 'OpenAlex Connector', 'Research metadata source status, cache policy, and fallback notes.'],
            'sc_public_crossref_connector' => ['crossref', 'Crossref Connector', 'Publication metadata source status, cache policy, and fallback notes.'],
            'sc_public_github_connector' => ['github', 'GitHub Connector', 'Repository intelligence source status, cache policy, and fallback notes.'],
            'sc_public_environmental_connectors' => ['environmental', 'Environmental Connectors', 'NASA, NOAA, EPA, EIA, USGS, GBIF, and Climate TRACE public source status.'],
            'sc_public_sustainable_development_sources' => ['sustainable-development-sources', 'Sustainable Development Public Sources', 'Planetary boundaries, SDGs, poverty, education, food, water, climate, and human-development sources.'],
            'sc_public_sustainable_development_families' => ['sustainable-development-families', 'Sustainable Development Connector Families', 'Connector coverage across environmental limits and human development.'],
            'sc_public_planetary_boundaries_registry' => ['planetary-boundaries', 'Planetary Boundaries Adapter Registry', 'Nine-boundary definitions, control variables, source mappings, and assessment status.'],
            'sc_public_sustainable_development_source_health' => ['sustainable-development-health', 'Sustainable Development Source Health', 'Freshness, cache, fallback, and public availability status.'],
            'sc_public_sustainable_development_methodology' => ['sustainable-development-methodology', 'Sustainable Development Data Methodology', 'Observation schema, provenance, freshness, and derived-assessment boundaries.'],
            'sc_public_sustainable_development_connector_reliability' => ['sustainable-development-reliability', 'Connector Reliability', 'Retry, circuit-breaker, schema, rate-limit, and last-known-good status.'],
            'sc_public_sustainable_development_freshness' => ['sustainable-development-freshness', 'Data Freshness Policy', 'Fresh, aging, stale, and last-known-good thresholds by public source.'],
            'sc_public_sustainable_development_schema_validation' => ['sustainable-development-schema-validation', 'Schema Validation', 'Registry and normalized observation schema readiness.'],
            'sc_public_sustainable_development_cache_status' => ['sustainable-development-cache', 'Connector Cache Status', 'Fresh, stale-servable, expired, and empty cache states.'],
            'sc_planetary_boundaries_observatory' => ['planetary-boundaries-observatory', 'Planetary Boundaries Observatory', 'Nine-boundary overview with scientific status, coverage, sources, and safe-operating-space context.'],
            'sc_planetary_boundary_overview' => ['planetary-boundaries-observatory', 'Planetary Boundary Overview', 'Public overview of all nine planetary boundaries.'],
            'sc_planetary_boundary_sources' => ['planetary-boundary-sources', 'Planetary Boundary Sources', 'Source registry and scientific references supporting the observatory.'],
            'sc_planetary_boundary_methodology' => ['planetary-boundary-methodology', 'Planetary Boundaries Methodology', 'Scientific-status labels, coverage rules, provenance, and derived-assessment boundaries.'],
            'sc_planetary_boundary_export' => ['planetary-boundary-export', 'Planetary Boundaries Export', 'Public-safe JSON and CSV-ready observatory records with source and methodology metadata.'],
            'sc_humanitarian_intelligence_observatory' => ['humanitarian-intelligence', 'Live Disaster, Displacement, and Humanitarian Intelligence', 'Source-aware links between physical hazards, humanitarian reporting, and displacement context.'],
            'sc_global_crisis_map' => ['humanitarian-crisis-map', 'Global Crisis Map', 'Map-ready GDACS, USGS, NASA EONET, ReliefWeb, and UNHCR layers.'],
            'sc_humanitarian_report_stream' => ['humanitarian-reports', 'Humanitarian Report Stream', 'ReliefWeb-ready reports, assessments, maps, and situation updates.'],
            'sc_displacement_context' => ['displacement-context', 'Displacement Context', 'UNHCR population categories, reference periods, and humanitarian context.'],
            'sc_humanitarian_intelligence_sources' => ['humanitarian-sources', 'Humanitarian Intelligence Sources', 'Public source registry, freshness, attribution, and limitations.'],
            'sc_humanitarian_intelligence_methodology' => ['humanitarian-methodology', 'Humanitarian Intelligence Methodology', 'Normalized event schema and public safety boundaries.'],
            'sc_humanitarian_intelligence_export' => ['humanitarian-export', 'Humanitarian Intelligence Export', 'Public-safe source, category, schema, and layer records.'],
            'sc_human_development_observatory' => ['human-development', 'Human Development and Social Conditions', 'Poverty, inequality, health, education, work, food security, water, sanitation, and source-aware context.'],
            'sc_human_development_sources' => ['human-development-sources', 'Human Development Sources', 'Official source registry, freshness, coverage, methodology, and limitations.'],
            'sc_human_development_inequalities' => ['human-development-inequalities', 'Inequality and Disaggregation', 'Sex, age, wealth, education, residence, disability, geography, and other available dimensions.'],
            'sc_human_development_methodology' => ['human-development-methodology', 'Human Development Methodology', 'Reference periods, modeled estimates, revisions, comparability, and aggregation rules.'],
            'sc_human_development_export' => ['human-development-export', 'Human Development Export', 'Public-safe source, domain, schema, and disaggregation records.'],
            'sc_international_law_governance_monitor' => ['international-law', 'International Law and Global Governance Monitor', 'Sanctions, treaties, UN decisions, courts, human rights, EU law, and trade governance.'],
            'sc_international_law_sources' => ['international-law-sources', 'International Law Sources', 'Official source registry, freshness, legal status, identifiers, and limitations.'],
            'sc_un_sanctions_monitor' => ['international-law-sanctions', 'UN Sanctions Monitor', 'Official consolidated-list changes, regimes, listings, amendments, and delistings.'],
            'sc_international_law_methodology' => ['international-law-methodology', 'International Law Methodology', 'Legal-event schema, procedural status, provenance, and human-review boundaries.'],
            'sc_international_law_export' => ['international-law-export', 'International Law Export', 'Public-safe sources, monitors, schemas, and methodology records.'],
            'sc_conflict_human_security_monitor' => ['human-security', 'Conflict, Displacement, and Human Security', 'Conflict events, civilian protection, displacement, infrastructure disruption, humanitarian access, and modeled risk.'],
            'sc_human_security_sources' => ['human-security-sources', 'Human Security Sources', 'ACLED, UCDP, UNHCR, IOM DTM, ReliefWeb, and HDX source registry.'],
            'sc_forced_displacement_flows' => ['human-security-displacement', 'Forced Displacement and Mobility', 'Refugee, asylum, internal displacement, return, statelessness, and mobility context.'],
            'sc_modeled_human_security_risk' => ['human-security-modeled-risk', 'Modeled Human Security Risk', 'Forecast metadata, confidence, horizons, model versions, and limitations.'],
            'sc_human_security_methodology' => ['human-security-methodology', 'Human Security Methodology', 'Event, displacement, protection, infrastructure, forecast, and responsible-data rules.'],
            'sc_human_security_export' => ['human-security-export', 'Human Security Export', 'Public-safe sources, monitors, schemas, and methodology records.'],
            'sc_public_dashboard_studio' => ['cross-domain-dashboard-studio', 'Cross-Domain Intelligence and Public Dashboard Studio', 'Configuration-driven public dashboards, country profiles, comparisons, source panels, briefs, and exports.'],
            'sc_public_dashboard_launch_manifest' => ['dashboard-launch-manifest', 'Public Dashboard Launch Manifest', 'Launch-ready navigation, interaction states, accessibility, source transparency, and export contracts.'],
            'sc_public_dashboard_launch_readiness' => ['dashboard-launch-readiness', 'Public Dashboard Launch Readiness', 'Required and recommended checks for a polished production launch.'],
            'sc_public_dashboard_studio_navigation' => ['dashboard-public-navigation', 'Public Dashboard Navigation', 'Public navigation across dashboards, country profiles, comparisons, sources, methodology, and exports.'],
            'sc_public_cross_domain_dashboard_directory' => ['cross-domain-dashboard-directory', 'Public Intelligence Dashboard Directory', 'Browse flagship cross-domain dashboards and country intelligence experiences.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['connector-status', 'Public Connector Status', 'Loading public connector status…'];
    }

    public function public_connector_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_connector_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-connector-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Connector Layer</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    public function planetary_boundary_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'climate-change'], $atts, 'sc_planetary_boundary');
        return $this->planetary_boundary_panel_markup('planetary-boundary-detail', sanitize_title($atts['id']), 'Planetary Boundary Detail');
    }

    public function planetary_boundary_trend_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'climate-change'], $atts, 'sc_planetary_boundary_trend');
        return $this->planetary_boundary_panel_markup('planetary-boundary-trend', sanitize_title($atts['id']), 'Planetary Boundary Trend');
    }

    private function planetary_boundary_panel_markup($panel, $boundary_id, $title) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-public-connector-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel); ?>" data-boundary-id="<?php echo esc_attr($boundary_id); ?>">
            <p class="scsi-eyebrow">Planetary Boundaries Observatory</p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted">Loading source-aware boundary context…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function international_law_monitor_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'sanctions'], $atts, 'sc_international_law_monitor');
        return $this->international_law_panel_markup('international-law-monitor', sanitize_title($atts['id']), '', '', 'International Law Monitor');
    }

    public function international_law_event_stream_shortcode($atts = []) {
        $atts = shortcode_atts(['event_type' => '', 'jurisdiction' => ''], $atts, 'sc_international_law_event_stream');
        return $this->international_law_panel_markup('international-law-events', '', sanitize_text_field($atts['event_type']), sanitize_text_field($atts['jurisdiction']), 'International Law Event Stream');
    }

    private function international_law_panel_markup($panel, $monitor_id, $event_type, $jurisdiction, $title) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-public-connector-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel); ?>" data-monitor-id="<?php echo esc_attr($monitor_id); ?>" data-event-type="<?php echo esc_attr($event_type); ?>" data-jurisdiction="<?php echo esc_attr($jurisdiction); ?>">
            <p class="scsi-eyebrow">International Law and Global Governance</p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted">Loading source-aware official-record context…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function human_security_monitor_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'conflict-events'], $atts, 'sc_human_security_monitor');
        return $this->human_security_panel_markup('human-security-monitor', sanitize_title($atts['id']), '', '', 'Human Security Monitor');
    }

    public function human_security_event_stream_shortcode($atts = []) {
        $atts = shortcode_atts(['record_type' => '', 'country' => ''], $atts, 'sc_conflict_event_stream');
        return $this->human_security_panel_markup('human-security-events', '', sanitize_text_field($atts['record_type']), sanitize_text_field($atts['country']), 'Conflict and Human Security Event Stream');
    }

    private function human_security_panel_markup($panel, $monitor_id, $record_type, $country, $title) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-public-connector-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel); ?>" data-monitor-id="<?php echo esc_attr($monitor_id); ?>" data-record-type="<?php echo esc_attr($record_type); ?>" data-country="<?php echo esc_attr($country); ?>">
            <p class="scsi-eyebrow">Conflict, Displacement, and Human Security</p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted">Loading source-aware conflict, protection, displacement, and humanitarian-access context…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function human_development_domain_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'poverty'], $atts, 'sc_human_development_domain');
        return $this->human_development_panel_markup('human-development-domain', sanitize_title($atts['id']), '', 'Human Development Domain');
    }

    public function human_development_country_profile_shortcode($atts = []) {
        $atts = shortcode_atts(['country' => ''], $atts, 'sc_human_development_country_profile');
        return $this->human_development_panel_markup('human-development-country-profile', '', sanitize_text_field($atts['country']), 'Human Development Country Profile');
    }

    private function human_development_panel_markup($panel, $domain_id, $country, $title) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-public-connector-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel); ?>" data-domain-id="<?php echo esc_attr($domain_id); ?>" data-country="<?php echo esc_attr($country); ?>">
            <p class="scsi-eyebrow">Human Development and Social Conditions</p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted">Loading source-aware social-condition context…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }






    public function source_methodology_studio_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1100',
            'title' => 'Sustainable Catalyst Source and Methodology Studio',
            'source' => '',
            'domain' => '',
            'state' => '',
            'feature' => '',
            'query' => '',
        ], $atts, 'sc_source_methodology_studio');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding the Source and Methodology Studio.</div>';
        }

        $height = max(820, min(1900, absint($atts['height'])));
        $params = ['view' => 'sources'];

        $source = sanitize_title((string) $atts['source']);
        if ($source !== '') {
            $params['source'] = $source;
        }

        $domain = sanitize_title((string) $atts['domain']);
        if ($domain !== '') {
            $params['domain'] = $domain;
        }

        $allowed_states = ['live', 'cached', 'stale', 'temporarily-unavailable', 'experimental', 'disabled'];
        $state = sanitize_title((string) $atts['state']);
        if (in_array($state, $allowed_states, true)) {
            $params['state'] = $state;
        }

        $feature = sanitize_title((string) $atts['feature']);
        if ($feature !== '') {
            $params['feature'] = $feature;
        }

        $query = sanitize_text_field((string) $atts['query']);
        if ($query !== '') {
            $params['query'] = $query;
        }

        $src = esc_url($backend . '/app/?' . http_build_query($params, '', '&', PHP_QUERY_RFC3986));
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-source-methodology-embed"><div class="scsi-app-loading">Opening Source and Methodology Studio…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }


    public function saved_research_views_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1000',
            'title' => 'Sustainable Catalyst Saved Views and Shareable Research Paths',
        ], $atts, 'sc_saved_research_views');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding Saved Views and Shareable Research Paths.</div>';
        }

        $height = max(760, min(1900, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=saved');
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-saved-research-views-embed"><div class="scsi-app-loading">Opening Saved Views and Shareable Research Paths…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }


    public function thematic_intelligence_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1150',
            'title' => 'Sustainable Catalyst Thematic Intelligence Dashboards',
            'dashboard' => 'climate-environment',
            'country' => 'KEN',
            'days' => '30',
        ], $atts, 'sc_thematic_intelligence');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding Thematic Intelligence.</div>';
        }

        $allowed_dashboards = [
            'climate-environment',
            'human-development',
            'human-security',
            'infrastructure',
        ];
        $dashboard = sanitize_title((string) $atts['dashboard']);
        if (!in_array($dashboard, $allowed_dashboards, true)) {
            $dashboard = 'climate-environment';
        }

        $country_input = strtoupper(trim((string) $atts['country']));
        $country = preg_match('/^[A-Z]{3}$/', $country_input) ? $country_input : 'KEN';
        $days = max(1, min(90, absint($atts['days'])));
        if ($days === 0) {
            $days = 30;
        }
        $height = max(850, min(1900, absint($atts['height'])));

        $query = [
            'view' => 'thematic',
            'dashboard' => $dashboard,
            'country' => $country,
            'thematicDays' => $days,
        ];
        $src = esc_url($backend . '/app/?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986));
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-thematic-intelligence-embed"><div class="scsi-app-loading">Opening Thematic Intelligence…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }


    public function public_briefing_studio_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1150',
            'title' => 'Sustainable Catalyst Public Briefing and Export Studio',
            'type' => 'country',
            'country' => 'KEN',
            'compare' => 'GHA',
            'days' => '14',
            'event_id' => '',
            'dashboard_id' => 'climate-environment',
            'layer_id' => 'true-color',
            'date_a' => '',
            'date_b' => '',
        ], $atts, 'sc_public_briefing_studio');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding the Public Briefing and Export Studio.</div>';
        }

        $height = max(860, min(1900, absint($atts['height'])));
        $allowed_types = ['country', 'comparison', 'event', 'earth', 'thematic'];
        $type = sanitize_key((string) $atts['type']);
        if (!in_array($type, $allowed_types, true)) {
            $type = 'country';
        }

        $country_input = strtoupper(trim((string) $atts['country']));
        $compare_input = strtoupper(trim((string) $atts['compare']));
        $country = preg_match('/^[A-Z]{3}$/', $country_input) ? $country_input : 'KEN';
        $compare = preg_match('/^[A-Z]{3}$/', $compare_input) ? $compare_input : 'GHA';
        if ($compare === $country) {
            $compare = $country === 'GHA' ? 'KEN' : 'GHA';
        }

        $days = max(1, min(90, absint($atts['days'])));
        if ($days === 0) {
            $days = 14;
        }

        $query = [
            'view' => 'briefing',
            'briefType' => $type,
            'type' => $type,
            'country' => $country,
            'compare' => $compare,
            'days' => $days,
        ];

        $event_id = sanitize_text_field((string) $atts['event_id']);
        if ($event_id !== '' && preg_match('/^[A-Za-z0-9._-]{1,96}$/', $event_id)) {
            $query['event_id'] = $event_id;
        }

        $dashboard_id = sanitize_title((string) $atts['dashboard_id']);
        if ($dashboard_id !== '') {
            $query['dashboard_id'] = $dashboard_id;
        }

        $layer_id = sanitize_title((string) $atts['layer_id']);
        if ($layer_id !== '') {
            $query['layer_id'] = $layer_id;
        }

        foreach (['date_a', 'date_b'] as $date_key) {
            $value = sanitize_text_field((string) $atts[$date_key]);
            if ($value !== '' && preg_match('/^\d{4}-\d{2}-\d{2}$/', $value)) {
                $query[$date_key] = $value;
            }
        }

        $src = esc_url($backend . '/app/?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986));
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-public-briefing-studio-embed"><div class="scsi-app-loading">Opening Public Briefing and Export Studio…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }


    public function comparative_intelligence_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1100',
            'title' => 'Sustainable Catalyst Comparative Intelligence and Briefing Studio',
            'country' => 'KEN',
            'compare' => 'GHA',
            'view' => 'table',
            'indicator' => '',
        ], $atts, 'sc_comparative_intelligence');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding Comparative Intelligence.</div>';
        }

        $height = max(820, min(1800, absint($atts['height'])));
        $country_input = strtoupper(trim((string) $atts['country']));
        $compare_input = strtoupper(trim((string) $atts['compare']));
        $country = preg_match('/^[A-Z]{3}$/', $country_input) ? $country_input : 'KEN';
        $compare = preg_match('/^[A-Z]{3}$/', $compare_input) ? $compare_input : 'GHA';
        if ($compare === $country) {
            $compare = $country === 'GHA' ? 'KEN' : 'GHA';
        }

        $allowed_views = ['table', 'chart', 'map', 'brief', 'export'];
        $view = sanitize_key((string) $atts['view']);
        if (!in_array($view, $allowed_views, true)) {
            $view = 'table';
        }

        $indicator = sanitize_text_field((string) $atts['indicator']);
        if (!preg_match('/^[A-Za-z0-9._-]{1,64}$/', $indicator)) {
            $indicator = '';
        }

        $query = [
            'view' => 'compare',
            'country' => $country,
            'compare' => $compare,
            'compareView' => $view,
        ];
        if ($indicator !== '') {
            $query['indicator'] = $indicator;
        }
        $src = esc_url($backend . '/app/?' . http_build_query($query, '', '&', PHP_QUERY_RFC3986));
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-comparative-intelligence-embed"><div class="scsi-app-loading">Opening Comparative Intelligence…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }

    public function global_country_intelligence_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1100',
            'title' => 'Sustainable Catalyst Global Country Intelligence',
            'country' => 'KEN',
        ], $atts, 'sc_global_country_intelligence');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding Global Country Intelligence.</div>';
        }

        $height = max(760, min(1800, absint($atts['height'])));
        $country = strtoupper(preg_replace('/[^A-Za-z]/', '', (string) $atts['country']));
        if (strlen($country) !== 3) {
            $country = 'KEN';
        }
        $src = esc_url($backend . '/app/?view=country&country=' . rawurlencode($country));
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-global-country-embed"><div class="scsi-app-loading">Opening Global Country Intelligence…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }

    public function live_event_intelligence_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1000',
            'title' => 'Sustainable Catalyst Live Event Intelligence',
        ], $atts, 'sc_live_event_intelligence');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding Live Event Intelligence.</div>';
        }

        $height = max(700, min(1600, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=events');
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-live-events-embed"><div class="scsi-app-loading">Opening Live Event Intelligence…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }

    public function earth_observation_studio_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1000',
            'title' => 'Sustainable Catalyst Earth Observation Studio',
        ], $atts, 'sc_earth_observation_studio');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding Earth Observation Studio.</div>';
        }

        $height = max(700, min(1600, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=earth');
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-earth-studio-embed"><div class="scsi-app-loading">Opening Earth Observation Studio…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }

    public function auditable_public_observatory_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1250',
            'title' => 'Sustainable Catalyst Auditable Public Observatory',
        ], $atts, 'sc_auditable_public_observatory');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding the Auditable Public Observatory.</div>';
        }

        $height = max(850, min(2000, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=observatory');
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-auditable-observatory-embed"><div class="scsi-app-loading">Opening the Auditable Public Observatory…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }

    public function site_intelligence_launch_shortcode($atts = []) {
        $atts = shortcode_atts([
            'height' => '1200',
            'title' => 'Sustainable Catalyst Site Intelligence Public Launch and Portfolio',
        ], $atts, 'sc_site_intelligence_launch');

        $options = self::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding the public launch and portfolio view.</div>';
        }

        $height = max(800, min(1900, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=launch');
        $title = esc_attr((string) $atts['title']);

        return sprintf(
            '<div class="scsi-standalone-app scsi-site-intelligence-launch-embed"><div class="scsi-app-loading">Opening the Site Intelligence public launch…</div><iframe src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe></div>',
            $src,
            $title,
            $height
        );
    }

    public function standalone_app_shortcode($atts = []) {
        $options = self::options();
        $atts = shortcode_atts([
            'height' => '900',
            'title' => 'Site Intelligence application',
            'path' => '/app/',
        ], $atts, 'sc_site_intelligence_app');

        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if (!$backend) {
            return '<div class="scsi-app-error">Configure the Site Intelligence backend URL before embedding the standalone application.</div>';
        }

        $height = max(620, min(1400, absint($atts['height'])));
        $src = esc_url($backend . '/' . ltrim((string) $atts['path'], '/'));
        $title = esc_attr((string) $atts['title']);

        $frame_id = 'scsi-app-' . wp_generate_uuid4();
        return sprintf(
            '<div class="scsi-standalone-app" data-scsi-responsive-app><div class="scsi-app-loading">Opening Site Intelligence…</div><iframe id="%4$s" src="%1$s" title="%2$s" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="fullscreen; clipboard-write" style="width:100%%;height:%3$dpx;border:0;border-radius:18px;display:block;background:#05070a" onload="this.parentNode.classList.add(\'is-loaded\')"></iframe><script>(function(){var frame=document.getElementById(%5$s);if(!frame)return;var expectedOrigin=new URL(frame.src,window.location.href).origin;window.addEventListener(\'message\',function(e){if(e.origin!==expectedOrigin||!e.data||e.data.type!==\'scsi-height\')return;var h=Math.max(620,Math.min(1800,parseInt(e.data.height||0,10)+8));if(h)frame.style.height=h+\'px\';});})();</script></div>',
            $src,
            $title,
            $height,
            esc_attr($frame_id),
            wp_json_encode($frame_id)
        );
    }

    public function geospatial_map_shortcode($atts = [], $content = null, $tag = '') {
        $atts = shortcode_atts([
            'latitude' => '12',
            'longitude' => '20',
            'zoom' => '2',
            'height' => '1000',
            'date' => gmdate('Y-m-d'),
            'layer' => 'true-color',
        ], $atts, $tag ?: 'sc_geospatial_intelligence_map');

        $params = [
            'view' => 'earth',
            'latitude' => sanitize_text_field((string) $atts['latitude']),
            'longitude' => sanitize_text_field((string) $atts['longitude']),
            'zoom' => absint($atts['zoom']),
            'dateB' => sanitize_text_field((string) $atts['date']),
            'earthLayer' => sanitize_title((string) $atts['layer']),
        ];

        return $this->standalone_app_shortcode([
            'height' => max(700, min(1600, absint($atts['height']))),
            'title' => 'Sustainable Catalyst Earth Observation Studio',
            'path' => '/app/?' . http_build_query($params, '', '&', PHP_QUERY_RFC3986),
        ]);
    }

    public function geospatial_table_shortcode() {
        return '<section class="scsi-card scsi-geospatial-table-panel" data-scsi-geospatial-table><p class="scsi-eyebrow">Accessible Geospatial Data</p><h2>Live Event Table</h2><p class="scsi-muted">Loading event records…</p><div class="scsi-output"></div></section>';
    }

    public function geospatial_layer_directory_shortcode() {
        return '<section class="scsi-card scsi-geospatial-layer-directory" data-scsi-geospatial-layers><p class="scsi-eyebrow">Geospatial Layers</p><h2>Satellite and Map Layer Directory</h2><p class="scsi-muted">Loading public layer manifest…</p><div class="scsi-output"></div></section>';
    }

    public function cross_domain_dashboard_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'climate-human-vulnerability', 'country' => '', 'region' => '', 'compare' => '', 'view' => 'data'], $atts, 'sc_public_intelligence_dashboard');
        return $this->cross_domain_panel_markup('cross-domain-dashboard', sanitize_title($atts['id']), sanitize_text_field($atts['country']), sanitize_text_field($atts['region']), sanitize_text_field($atts['compare']), sanitize_key($atts['view']), 'Public Intelligence Dashboard');
    }

    public function country_intelligence_shortcode($atts = []) {
        $atts = shortcode_atts(['country' => 'KEN', 'height' => '1050'], $atts, 'sc_public_country_intelligence');
        $country = strtoupper(trim((string) $atts['country']));
        if (!preg_match('/^[A-Z]{3}$/', $country)) { $country = 'KEN'; }
        return $this->standalone_app_shortcode([
            'height' => max(700, min(1600, absint($atts['height']))),
            'title' => 'Sustainable Catalyst Global Country Intelligence',
            'path' => '/app/?view=country&country=' . rawurlencode($country),
        ]);
    }

    public function cross_domain_comparison_shortcode($atts = []) {
        $atts = shortcode_atts(['country' => 'KEN', 'compare' => 'GHA', 'height' => '1100'], $atts, 'sc_public_cross_domain_comparison');
        $country = strtoupper(trim((string) $atts['country']));
        $compare = strtoupper(trim((string) $atts['compare']));
        if (!preg_match('/^[A-Z]{3}$/', $country)) { $country = 'KEN'; }
        if (!preg_match('/^[A-Z]{3}$/', $compare)) { $compare = 'GHA'; }
        return $this->standalone_app_shortcode([
            'height' => max(760, min(1700, absint($atts['height']))),
            'title' => 'Sustainable Catalyst Comparative Intelligence',
            'path' => '/app/?view=compare&country=' . rawurlencode($country) . '&compare=' . rawurlencode($compare),
        ]);
    }

    public function cross_domain_dashboard_sources_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'climate-human-vulnerability'], $atts, 'sc_public_dashboard_sources');
        return $this->cross_domain_panel_markup('cross-domain-dashboard-sources', sanitize_title($atts['id']), '', '', '', '', 'Dashboard Sources');
    }

    public function cross_domain_dashboard_export_shortcode($atts = []) {
        $atts = shortcode_atts(['id' => 'climate-human-vulnerability', 'country' => ''], $atts, 'sc_public_dashboard_export');
        return $this->cross_domain_panel_markup('cross-domain-dashboard-export', sanitize_title($atts['id']), sanitize_text_field($atts['country']), '', '', '', 'Dashboard Export');
    }

    private function cross_domain_panel_markup($panel, $dashboard_id, $country, $region, $compare, $view, $title) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-public-connector-panel scsi-cross-domain-panel scsi-launch-ready-panel" data-scsi-public-connector-panel data-connector-panel="<?php echo esc_attr($panel); ?>" data-dashboard-id="<?php echo esc_attr($dashboard_id); ?>" data-country="<?php echo esc_attr($country); ?>" data-region="<?php echo esc_attr($region); ?>" data-compare="<?php echo esc_attr($compare); ?>" data-view="<?php echo esc_attr($view); ?>">
            <div class="scsi-public-dashboard-header">
                <div>
                    <p class="scsi-eyebrow">Sustainable Catalyst Site Intelligence</p>
                    <h2><?php echo esc_html($title); ?></h2>
                    <p class="scsi-muted">Source-aware evidence across environmental limits, human development, humanitarian conditions, conflict, displacement, and international law.</p>
                </div>
                <div class="scsi-public-dashboard-actions" aria-label="Dashboard actions">
                    <button type="button" class="scsi-public-action" data-scsi-copy-view>Copy view link</button>
                    <button type="button" class="scsi-public-action" data-scsi-print-view>Print view</button>
                </div>
            </div>
            <nav class="scsi-public-dashboard-nav" aria-label="Site Intelligence dashboard sections">
                <a href="#dashboard-directory">Dashboards</a><a href="#country-intelligence">Country profiles</a><a href="#compare-places">Compare places</a><a href="#sources">Sources</a><a href="#methodology">Methodology</a>
            </nav>
            <div class="scsi-loading-shell" role="status" aria-live="polite">
                <span class="scsi-skeleton scsi-skeleton-title"></span>
                <span class="scsi-skeleton"></span>
                <span class="scsi-skeleton"></span>
                <span class="screen-reader-text">Loading current evidence.</span>
            </div>
            <div class="scsi-output" aria-live="polite" aria-atomic="false"></div>
            <noscript><p class="scsi-public-state scsi-public-state-error">JavaScript is required for the interactive dashboard. Source and methodology endpoints remain available.</p></noscript>
        </section>
        <?php return ob_get_clean();
    }

    private function public_indicator_chart_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_indicator_dashboard_directory' => ['directory', 'Public Indicator Dashboard Directory', 'Chart-ready public indicator dashboards for Site Intelligence.'],
            'sc_public_sustainability_indicator_dashboard' => ['sustainability', 'Sustainability Indicator Dashboard', 'Charts for sustainability indicators, source status, and connector reliability.'],
            'sc_public_development_indicator_dashboard' => ['development', 'Development Indicator Dashboard', 'Charts for World Bank, OECD, and UN/SDG indicator context.'],
            'sc_public_source_health_chart_dashboard' => ['source-health', 'Source Health Chart Dashboard', 'Charts for source family status, reliability, cache, and fallback readiness.'],
            'sc_public_research_metadata_chart_dashboard' => ['research', 'Research Metadata Chart Dashboard', 'Charts for OpenAlex and Crossref metadata context.'],
            'sc_public_repository_chart_dashboard' => ['repository', 'Repository Intelligence Chart Dashboard', 'Charts for GitHub repository intelligence and public code-infrastructure context.'],
            'sc_public_indicator_chart_gallery' => ['gallery', 'Indicator Chart Gallery', 'Combined public chart gallery for indicator dashboard review.'],
            'sc_public_indicator_chart_visual_qa' => ['visual-qa', 'Indicator Chart Visual QA', 'Visual QA for chart payloads, shortcodes, and public display.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['directory', 'Public Indicator Dashboard Directory', 'Loading public indicator dashboards…'];
    }

    public function public_indicator_chart_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_indicator_chart_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-indicator-chart-panel" data-scsi-public-indicator-chart-panel data-indicator-chart-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Indicator Chart Layer</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }



    private function public_source_aware_brief_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_source_aware_brief_directory' => ['directory', 'Source-Aware Brief Directory', 'Public-safe brief directory for Site Intelligence source context.'],
            'sc_public_site_intelligence_source_brief' => ['site-intelligence', 'Site Intelligence Source-Aware Brief', 'Dashboard, source, connector, and indicator context in one reviewed brief.'],
            'sc_public_indicator_source_brief' => ['indicator', 'Indicator Dashboard Source Brief', 'Source-aware interpretation for public indicator dashboards and charts.'],
            'sc_public_source_health_brief' => ['source-health', 'Source Health Brief', 'Connector reliability, cache/fallback status, freshness, and disclosure notes.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['directory', 'Source-Aware Brief Directory', 'Loading public source-aware briefs…'];
    }

    public function public_source_aware_brief_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_source_aware_brief_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-source-aware-brief-panel" data-scsi-public-source-aware-brief-panel data-source-brief-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Source-Aware Briefs</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php
        return ob_get_clean();
    }

    private function public_dashboard_export_panel_from_shortcode_tag($tag) {
        $map = [
            'sc_public_dashboard_export_manifest' => ['manifest', 'Public Dashboard Export Manifest', 'Export-ready public dashboard/source/brief bundle directory.'],
            'sc_public_site_intelligence_export' => ['site-intelligence', 'Site Intelligence Public Export', 'Copy-ready public export for the full Site Intelligence layer.'],
            'sc_public_indicator_dashboard_export' => ['indicator', 'Indicator Dashboard Export', 'Copy-ready export for indicator dashboards, chart summaries, and source citations.'],
            'sc_public_source_health_export' => ['source-health', 'Source Health Export', 'Copy-ready export for source health, freshness, and connector reliability.'],
            'sc_public_dashboard_export_visual_qa' => ['visual-qa', 'Dashboard Export Visual QA', 'Visual QA for export cards, public citations, and Markdown copies.'],
        ];
        return isset($map[$tag]) ? $map[$tag] : ['manifest', 'Public Dashboard Export Manifest', 'Loading public dashboard exports…'];
    }

    public function public_dashboard_export_panel_shortcode($atts = [], $content = null, $tag = '') {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') {
            return '';
        }
        $panel = $this->public_dashboard_export_panel_from_shortcode_tag($tag);
        ob_start();
        ?>
        <section class="scsi-card scsi-public-dashboard-export-panel" data-scsi-public-dashboard-export-panel data-dashboard-export-panel="<?php echo esc_attr($panel[0]); ?>">
            <p class="scsi-eyebrow">Public Dashboard Exports</p>
            <h2><?php echo esc_html($panel[1]); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($panel[2]); ?></p>
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


    private function report_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'prior_start_date' => '',
            'prior_end_date' => '',
            'limit' => '',
            'latitude' => '',
            'longitude' => '',
            'country' => '',
            'start' => '',
            'end' => '',
            'year' => '',
            'live' => '',
            'report' => '',
        ], $atts, $shortcode);
    }

    private function report_shortcode($atts, $shortcode, $type, $eyebrow, $title, $loading) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->report_shortcode_atts($atts, $shortcode);
        ob_start(); ?>
        <section class="scsi-card scsi-report-card" data-scsi-report data-report-type="<?php echo esc_attr($type); ?>"
            data-start-date="<?php echo esc_attr($atts['start_date']); ?>" data-end-date="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start-date="<?php echo esc_attr($atts['prior_start_date']); ?>" data-prior-end-date="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>" data-latitude="<?php echo esc_attr($atts['latitude']); ?>" data-longitude="<?php echo esc_attr($atts['longitude']); ?>"
            data-country="<?php echo esc_attr($atts['country']); ?>" data-start="<?php echo esc_attr($atts['start']); ?>" data-end="<?php echo esc_attr($atts['end']); ?>"
            data-year="<?php echo esc_attr($atts['year']); ?>" data-live="<?php echo esc_attr($atts['live']); ?>" data-report="<?php echo esc_attr($atts['report']); ?>">
            <p class="scsi-eyebrow"><?php echo esc_html($eyebrow); ?></p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($loading); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function site_intelligence_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_site_intelligence_report', 'site-intelligence', 'Report Generator', 'Weekly Site Intelligence Report', 'Loading Site Intelligence report…');
    }

    public function search_intelligence_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_search_intelligence_report', 'search-intelligence', 'Search Report', 'Search Intelligence Report', 'Loading Search Intelligence report…');
    }

    public function content_strategy_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_content_strategy_report', 'content-strategy', 'Publishing Report', 'Content Strategy Report', 'Loading Content Strategy report…');
    }

    public function external_sources_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_external_sources_report', 'external-sources', 'External Sources Report', 'External Data Source Brief', 'Loading External Sources report…');
    }

    public function climate_energy_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_climate_energy_report', 'climate-energy', 'Climate + Energy Report', 'Climate + Energy Snapshot Report', 'Loading Climate + Energy report…');
    }

    public function indexing_report_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_indexing_report', 'indexing', 'Indexing Report', 'Registry and Indexing Coverage Report', 'Loading Indexing Coverage report…');
    }

    public function report_export_bundle_shortcode($atts = []) {
        return $this->report_shortcode($atts, 'sc_report_export_bundle', 'export', 'Export Bundle', 'Site Intelligence Export Bundle', 'Loading export bundle summary…');
    }


    private function ai_brief_shortcode_atts($atts, $shortcode) {
        return shortcode_atts([
            'start_date' => '',
            'end_date' => '',
            'prior_start_date' => '',
            'prior_end_date' => '',
            'limit' => '',
            'mode' => '',
            'use_ai' => '',
            'live' => '',
        ], $atts, $shortcode);
    }

    public function ai_brief_status_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        ob_start(); ?>
        <section class="scsi-card scsi-ai-status" data-scsi-ai-status>
            <p class="scsi-eyebrow">AI Briefs</p>
            <h2>AI Brief Provider Status</h2>
            <p class="scsi-muted">Loading AI provider status…</p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    private function ai_brief_shortcode($atts, $shortcode, $type, $eyebrow, $title, $loading) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = $this->ai_brief_shortcode_atts($atts, $shortcode);
        ob_start(); ?>
        <section class="scsi-card scsi-ai-brief-card" data-scsi-ai-brief data-brief-type="<?php echo esc_attr($type); ?>"
            data-start-date="<?php echo esc_attr($atts['start_date']); ?>" data-end-date="<?php echo esc_attr($atts['end_date']); ?>"
            data-prior-start-date="<?php echo esc_attr($atts['prior_start_date']); ?>" data-prior-end-date="<?php echo esc_attr($atts['prior_end_date']); ?>"
            data-limit="<?php echo esc_attr($atts['limit']); ?>" data-mode="<?php echo esc_attr($atts['mode']); ?>" data-use-ai="<?php echo esc_attr($atts['use_ai']); ?>" data-live="<?php echo esc_attr($atts['live']); ?>">
            <p class="scsi-eyebrow"><?php echo esc_html($eyebrow); ?></p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($loading); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function ai_site_intelligence_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_site_intelligence_brief', 'site-intelligence', 'AI-Assisted Brief', 'Weekly Site Intelligence Brief', 'Loading AI-assisted Site Intelligence brief…');
    }

    public function ai_search_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_search_brief', 'search', 'AI-Assisted Brief', 'Search Intelligence Brief', 'Loading AI-assisted Search brief…');
    }

    public function ai_publishing_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_publishing_brief', 'publishing', 'AI-Assisted Brief', 'Publishing Strategy Brief', 'Loading AI-assisted Publishing brief…');
    }

    public function ai_external_sources_brief_shortcode($atts = []) {
        return $this->ai_brief_shortcode($atts, 'sc_ai_external_sources_brief', 'external-sources', 'AI-Assisted Brief', 'External Data Sources Brief', 'Loading AI-assisted External Sources brief…');
    }

    public function ai_public_dashboard_brief_shortcode($atts = []) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        $atts = shortcode_atts([
            'live' => '',
        ], $atts, 'sc_ai_public_dashboard_brief');
        if ($atts['live'] === 'true' || $atts['live'] === '1') {
            return $this->ai_brief_shortcode($atts, 'sc_ai_public_dashboard_brief', 'public-dashboard', 'AI-Assisted Brief', 'Public Dashboard Brief', 'Loading AI-assisted Public Dashboard brief…');
        }
        $brief = $this->local_public_dashboard_ai_brief();
        ob_start(); ?>
        <section class="scsi-card scsi-ai-brief-card scsi-ai-public-dashboard-local">
            <p class="scsi-eyebrow">AI-Assisted Brief</p>
            <h2>Public Dashboard Brief</h2>
            <p class="scsi-muted">Provider: <?php echo esc_html($brief['provider']); ?> · Model: <?php echo esc_html($brief['model']); ?> · Mode: public · Source: local public-safe fallback</p>
            <div class="scsi-output" aria-live="polite">
                <div class="scsi-ai-summary"><h3>Executive summary</h3><p><?php echo esc_html($brief['executive_summary']); ?></p></div>
                <p class="scsi-muted scsi-ai-confidence">Confidence: <?php echo esc_html($brief['confidence']['level']); ?> · <?php echo esc_html($brief['confidence']['basis']); ?></p>
                <h3>Key findings</h3><ul class="scsi-list scsi-ai-list">
                    <?php foreach ($brief['key_findings'] as $item): ?><li><?php echo esc_html($item); ?></li><?php endforeach; ?>
                </ul>
                <h3>Recommended next actions</h3><ul class="scsi-list scsi-ai-list">
                    <?php foreach ($brief['recommended_actions'] as $item): ?><li><?php echo esc_html($item); ?></li><?php endforeach; ?>
                </ul>
                <h3>Risk and uncertainty notes</h3><ul class="scsi-list scsi-ai-list">
                    <?php foreach ($brief['risk_notes'] as $item): ?><li><?php echo esc_html($item); ?></li><?php endforeach; ?>
                </ul>
                <div class="scsi-ai-public-summary"><h3>Public-safe summary draft</h3><p><?php echo esc_html($brief['public_safe_summary']); ?></p></div>
            </div>
        </section>
        <?php return ob_get_clean();
    }


    private function admin_control_shortcode($type, $eyebrow, $title, $loading) {
        $options = self::options();
        if ($options['enable_dashboard'] !== '1') { return ''; }
        if (!current_user_can('manage_options')) {
            return '<section class="scsi-card scsi-admin-control-card"><p class="scsi-muted">Site Intelligence admin controls are private.</p></section>';
        }
        ob_start(); ?>
        <section class="scsi-card scsi-admin-control-card" data-scsi-admin-control data-admin-type="<?php echo esc_attr($type); ?>">
            <p class="scsi-eyebrow"><?php echo esc_html($eyebrow); ?></p>
            <h2><?php echo esc_html($title); ?></h2>
            <p class="scsi-muted"><?php echo esc_html($loading); ?></p>
            <div class="scsi-output" aria-live="polite"></div>
        </section>
        <?php return ob_get_clean();
    }

    public function admin_overview_shortcode($atts = []) {
        return $this->admin_control_shortcode('overview', 'Admin Control Plane', 'Site Intelligence Admin Overview', 'Loading registry, source, module, and diagnostic status…');
    }

    public function shortcode_catalog_shortcode($atts = []) {
        return $this->admin_control_shortcode('shortcodes', 'Admin Control Plane', 'Shortcode Catalog', 'Loading shortcode catalog and placement guidance…');
    }

    public function module_status_shortcode($atts = []) {
        return $this->admin_control_shortcode('modules', 'Admin Control Plane', 'Module Status Matrix', 'Loading module status and visibility matrix…');
    }

    public function diagnostic_summary_shortcode($atts = []) {
        return $this->admin_control_shortcode('diagnostic-summary', 'Admin Diagnostics', 'One-Click Diagnostic Summary', 'Loading backend, registry, source, module, shortcode, and visibility diagnostics…');
    }

    public function connection_check_shortcode($atts = []) {
        return $this->admin_control_shortcode('connection-check', 'Admin Diagnostics', 'Connection Check', 'Loading backend, token, registry, source, and public-readiness checks…');
    }

    public function release_status_shortcode($atts = []) {
        return $this->admin_control_shortcode('release-status', 'Public Flagship Release', 'Site Intelligence v1.12.1 Release Status', 'Loading release checklist, smoke-test guidance, public page metadata, and launch notes…');
    }

}



// Site Intelligence v2.1.0 global conditions shortcode
if (!function_exists('scsi_global_conditions_observatory_shortcode_v210')) {
    function scsi_global_conditions_observatory_shortcode_v210($atts = []) {
        $atts = shortcode_atts([
            'height' => '1150',
            'title' => 'Sustainable Catalyst Global Conditions and Live Map Observatory',
        ], $atts, 'sc_global_conditions_observatory');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding the Global Conditions Observatory.</div>';
        }
        $height = max(760, min(1900, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=global');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Global Conditions in a new tab</a></p></div>',
            $src,
            $title,
            $height
        );
    }
}
add_shortcode('sc_global_conditions_observatory', 'scsi_global_conditions_observatory_shortcode_v210');


// Site Intelligence v2.2.0 economics, markets, and sustainability shortcode
if (!function_exists('scsi_economics_sustainability_observatory_shortcode_v220')) {
    function scsi_economics_sustainability_observatory_shortcode_v220($atts = []) {
        $atts = shortcode_atts([
            'height' => '1250',
            'title' => 'Sustainable Catalyst Economics, Markets, and Sustainability Signals',
        ], $atts, 'sc_economics_sustainability_observatory');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding the Economics and Sustainability Observatory.</div>';
        }
        $height = max(820, min(2200, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=economics');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Economics and Sustainability Signals in a new tab</a></p></div>',
            $src,
            $title,
            $height
        );
    }
}
add_shortcode('sc_economics_sustainability_observatory', 'scsi_economics_sustainability_observatory_shortcode_v220');


// Site Intelligence v2.3.0 international law and global governance shortcode
if (!function_exists('scsi_international_law_governance_observatory_shortcode_v230')) {
    function scsi_international_law_governance_observatory_shortcode_v230($atts = []) {
        $atts = shortcode_atts([
            'height' => '1350',
            'title' => 'Sustainable Catalyst International Law and Global Governance Observatory',
        ], $atts, 'sc_international_law_governance_observatory');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding the International Law and Global Governance Observatory.</div>';
        }
        $height = max(860, min(2400, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=law');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open International Law and Global Governance in a new tab</a></p></div>',
            $src,
            $title,
            $height
        );
    }
}
add_shortcode('sc_international_law_governance_observatory', 'scsi_international_law_governance_observatory_shortcode_v230');


// Site Intelligence v2.4.0 scientific and Earth systems shortcode
if (!function_exists('scsi_scientific_earth_systems_observatory_shortcode_v240')) {
    function scsi_scientific_earth_systems_observatory_shortcode_v240($atts = []) {
        $atts = shortcode_atts([
            'height' => '1400',
            'title' => 'Sustainable Catalyst Scientific and Earth Systems Observatory',
        ], $atts, 'sc_scientific_earth_systems_observatory');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding the Scientific and Earth Systems Observatory.</div>';
        }
        $height = max(900, min(2600, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=science');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Scientific and Earth Systems Observatory in a new tab</a></p></div>',
            $src,
            $title,
            $height
        );
    }
}
add_shortcode('sc_scientific_earth_systems_observatory', 'scsi_scientific_earth_systems_observatory_shortcode_v240');



// Site Intelligence v2.5.0 humanitarian, conflict, and displacement shortcode
if (!function_exists('scsi_humanitarian_conflict_displacement_observatory_shortcode_v250')) {
    function scsi_humanitarian_conflict_displacement_observatory_shortcode_v250($atts = []) {
        $atts = shortcode_atts([
            'height' => '1450',
            'title' => 'Sustainable Catalyst Humanitarian, Conflict, and Displacement Observatory',
        ], $atts, 'sc_humanitarian_conflict_displacement_observatory');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding the Humanitarian, Conflict, and Displacement Observatory.</div>';
        }
        $height = max(920, min(2800, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=humanitarian');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Humanitarian, Conflict, and Displacement Observatory in a new tab</a></p></div>',
            $src, $title, $height
        );
    }
}
add_shortcode('sc_humanitarian_conflict_displacement_observatory', 'scsi_humanitarian_conflict_displacement_observatory_shortcode_v250');



// Site Intelligence v2.6.0 trade, energy, and resource-security shortcode
if (!function_exists('scsi_trade_energy_resource_security_observatory_shortcode_v260')) {
    function scsi_trade_energy_resource_security_observatory_shortcode_v260($atts = []) {
        $atts = shortcode_atts([
            'height' => '1450',
            'title' => 'Sustainable Catalyst Trade, Energy, and Resource Security Observatory',
        ], $atts, 'sc_trade_energy_resource_security_observatory');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding the Trade, Energy, and Resource Security Observatory.</div>';
        }
        $height = max(920, min(2800, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=resources');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Trade, Energy, and Resource Security Observatory in a new tab</a></p></div>',
            $src, $title, $height
        );
    }
}
add_shortcode('sc_trade_energy_resource_security_observatory', 'scsi_trade_energy_resource_security_observatory_shortcode_v260');

// Site Intelligence v2.7.0 unified country and regional dossier shortcode
if (!function_exists('scsi_country_regional_intelligence_dossiers_shortcode_v270')) {
    function scsi_country_regional_intelligence_dossiers_shortcode_v270($atts = []) {
        $atts = shortcode_atts([
            'height' => '1500',
            'title' => 'Sustainable Catalyst Unified Country and Regional Intelligence Dossiers',
        ], $atts, 'sc_country_regional_intelligence_dossiers');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding Unified Country and Regional Intelligence Dossiers.</div>';
        }
        $height = max(950, min(3000, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=dossiers');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Unified Country and Regional Intelligence Dossiers in a new tab</a></p></div>',
            $src, $title, $height
        );
    }
}
add_shortcode('sc_country_regional_intelligence_dossiers', 'scsi_country_regional_intelligence_dossiers_shortcode_v270');


// Site Intelligence v2.8.0 alerts, monitoring, and live-stream shortcode
if (!function_exists('scsi_alerts_monitoring_live_streams_shortcode_v280')) {
    function scsi_alerts_monitoring_live_streams_shortcode_v280($atts = []) {
        $atts = shortcode_atts([
            'height' => '1500',
            'title' => 'Sustainable Catalyst Alerts, Monitoring, and Live Intelligence Streams',
        ], $atts, 'sc_alerts_monitoring_live_intelligence');
        $options = SC_Site_Intelligence_Plugin::options();
        $backend = rtrim((string) ($options['backend_url'] ?? ''), '/');
        if ($backend === '') {
            return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding Alerts, Monitoring, and Live Intelligence Streams.</div>';
        }
        $height = max(950, min(3200, absint($atts['height'])));
        $src = esc_url($backend . '/app/?view=alerts');
        $title = esc_attr((string) $atts['title']);
        return sprintf(
            '<div class="scsi-app-shell"><iframe class="scsi-app-frame" src="%1$s" title="%2$s" loading="lazy" style="width:100%%;min-height:%3$dpx;border:0" allow="fullscreen; clipboard-write"></iframe><p class="scsi-app-fallback"><a href="%1$s" target="_blank" rel="noopener noreferrer">Open Alerts, Monitoring, and Live Intelligence Streams in a new tab</a></p></div>',
            $src, $title, $height
        );
    }
}
add_shortcode('sc_alerts_monitoring_live_intelligence', 'scsi_alerts_monitoring_live_streams_shortcode_v280');

register_activation_hook(__FILE__, ['SC_Site_Intelligence_Plugin', 'activate']);
new SC_Site_Intelligence_Plugin();


// Site Intelligence v2.9.0 Comparative Intelligence and Scenario Studio shortcode
if (!function_exists('scsi_comparative_scenario_studio_shortcode_v290')) {
    function scsi_comparative_scenario_studio_shortcode_v290($atts = []) {
        $atts = shortcode_atts(['height' => '1550'], $atts, 'sc_comparative_intelligence_scenario_studio');
        $height = max(800, min(2400, intval($atts['height'])));
        $backend = function_exists('scsi_backend_url') ? scsi_backend_url() : get_option('scsi_backend_url', '');
        if (!$backend) return '<div class="scsi-notice">Site Intelligence backend is not configured.</div>';
        $src = esc_url(rtrim($backend, '/') . '/app/?view=scenarios');
        return '<div class="scsi-embed scsi-scenario-studio"><iframe title="Comparative Intelligence and Scenario Studio" src="' . $src . '" style="width:100%;height:' . esc_attr($height) . 'px;border:0" loading="lazy" allowfullscreen></iframe></div>';
    }
}
add_shortcode('sc_comparative_intelligence_scenario_studio', 'scsi_comparative_scenario_studio_shortcode_v290');


// Site Intelligence v2.10.0 Research Paths, Saved Investigations, and Briefing Workflows shortcode
if (!function_exists('scsi_research_paths_workflows_shortcode_v2100')) {
    function scsi_research_paths_workflows_shortcode_v2100($atts = []) {
        $atts = shortcode_atts(['height' => '1650'], $atts, 'sc_research_paths_investigations');
        $height = max(900, min(2800, intval($atts['height'])));
        $backend = function_exists('scsi_backend_url') ? scsi_backend_url() : get_option('scsi_backend_url', '');
        if (!$backend) return '<div class="scsi-notice">Site Intelligence backend is not configured.</div>';
        $src = esc_url(rtrim($backend, '/') . '/app/?view=research');
        return '<div class="scsi-embed scsi-research-workflows"><iframe title="Research Paths, Saved Investigations, and Briefing Workflows" src="' . $src . '" style="width:100%;height:' . esc_attr($height) . 'px;border:0" loading="lazy" allow="clipboard-write; fullscreen"></iframe></div>';
    }
}
add_shortcode('sc_research_paths_investigations', 'scsi_research_paths_workflows_shortcode_v2100');

// Site Intelligence v2.11.0 Public Data API, Embeds, and Institutional Integration shortcodes
if (!function_exists('scsi_public_data_api_integration_shortcode_v2110')) {
    function scsi_public_data_api_integration_shortcode_v2110($atts = []) {
        $atts = shortcode_atts(['height' => '1500'], $atts, 'sc_public_data_api_integration');
        $height = max(760, min(2600, intval($atts['height'])));
        $backend = function_exists('scsi_backend_url') ? scsi_backend_url() : get_option('scsi_backend_url', '');
        if (!$backend) return '<div class="scsi-notice">Site Intelligence backend is not configured.</div>';
        $src = esc_url(rtrim($backend, '/') . '/app/?view=integration');
        return '<div class="scsi-embed scsi-public-data-integration"><iframe title="Public Data API, Embeds, and Institutional Integration" src="' . $src . '" style="width:100%;height:' . esc_attr($height) . 'px;border:0" loading="lazy" allow="clipboard-write; fullscreen"></iframe></div>';
    }
}
add_shortcode('sc_public_data_api_integration', 'scsi_public_data_api_integration_shortcode_v2110');

if (!function_exists('scsi_site_intelligence_embed_shortcode_v2110')) {
    function scsi_site_intelligence_embed_shortcode_v2110($atts = []) {
        $atts = shortcode_atts(['view' => 'overview', 'height' => '900', 'theme' => 'system', 'chrome' => 'compact', 'institution' => ''], $atts, 'sc_site_intelligence_embed');
        $allowed_views = ['overview','global','economics','law','science','humanitarian','resources','dossiers','alerts','scenarios','research','integration','experience','earth','country','events','compare','thematic','briefing','sources','saved','observatory','launch'];
        $view = sanitize_key($atts['view']);
        if (!in_array($view, $allowed_views, true)) $view = 'overview';
        $theme = in_array($atts['theme'], ['system','light','dark'], true) ? $atts['theme'] : 'system';
        $chrome = in_array($atts['chrome'], ['full','compact','none'], true) ? $atts['chrome'] : 'compact';
        $height = max(420, min(2200, intval($atts['height'])));
        $backend = function_exists('scsi_backend_url') ? scsi_backend_url() : get_option('scsi_backend_url', '');
        if (!$backend) return '<div class="scsi-notice">Site Intelligence backend is not configured.</div>';
        $query = ['view' => $view, 'embed' => '1', 'theme' => $theme, 'chrome' => $chrome];
        if (!empty($atts['institution'])) $query['institution'] = sanitize_text_field($atts['institution']);
        $src = esc_url(add_query_arg($query, rtrim($backend, '/') . '/app/'));
        return '<div class="scsi-embed scsi-generic-public-embed"><iframe title="Sustainable Catalyst Site Intelligence — ' . esc_attr($view) . '" src="' . $src . '" style="width:100%;height:' . esc_attr($height) . 'px;border:0" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="clipboard-write; fullscreen"></iframe></div>';
    }
}
add_shortcode('sc_site_intelligence_embed', 'scsi_site_intelligence_embed_shortcode_v2110');



if (!function_exists('scsi_offline_mobile_accessibility_performance_shortcode_v2120')) {
    function scsi_offline_mobile_accessibility_performance_shortcode_v2120($atts = []) {
        $atts = shortcode_atts(['height' => '1500'], $atts, 'sc_offline_mobile_accessibility_performance');
        $backend = get_option('scsi_backend_url', '');
        if (!$backend) return '<div class="scsi-notice">Configure the Site Intelligence backend URL before embedding Offline, Mobile, Accessibility, and Performance.</div>';
        $height = max(700, min(2400, intval($atts['height'])));
        $src = esc_url(rtrim($backend, '/') . '/app/?view=experience');
        return '<div class="scsi-embed scsi-offline-experience"><iframe title="Offline, Mobile, Accessibility, and Performance" src="' . $src . '" style="width:100%;height:' . esc_attr($height) . 'px;border:0" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="clipboard-write; fullscreen"></iframe></div>';
    }
}
add_shortcode('sc_offline_mobile_accessibility_performance', 'scsi_offline_mobile_accessibility_performance_shortcode_v2120');
