/*global Triage: true, jwerty: true*/

Triage.modules.pane = (function($, app) {
	"use strict";

	var errorId;
	var errorUrl;

	var updateTabPane = function() {
		var tab = $('.pane-active');
		if (tab.length) {
			var active = $('.pane-'+tab.data('view'));
			active.siblings().hide();
			active.show();
			app.trigger('error.viewed', errorId);
		}
	};

	var loadError = function() {
		$('.pane .pane-inner').load(errorUrl, function(){
			updateTabPane();
		});
	};

	var selectTab = function(tab) {

		if (!tab) {
			var current = $('.pane .pane-actions li.pane-active');
			if (current.length) {
				tab = current;
			} else {
				tab = $('.pane .pane-actions li:first-child');
			}
		}
		tab = $(tab);
		tab.siblings().removeClass('pane-active active');
		tab.addClass('pane-active active');
		updateTabPane();
	};

	var hidePane = function() {
		$('.pane').removeClass('pane-open');
		$('body').removeClass('pane-open');
		$('.pane-padding').height(0);
		$('.pane').find('.pane-active').removeClass('pane-active active');
	};

	var showPane = function() {
		$('.pane').addClass('pane-open');
		$('body').addClass('pane-open');
		$('.pane-padding').height($('.pane').height());
		selectTab();
	};

	var togglePane = function() {

		if ($('body').hasClass('pane-open')) {
			return hidePane();
		}
		return showPane();
	};

	var bindActions = function(self) {
		var $selector = $(self).parent();

		if ($selector.hasClass('pane-active')) {
			hidePane();
		}
		else {
			showPane();
			selectTab($selector);
		}
	};

	$('.pane').on("keydown", "textarea, input, select", jwerty.event('↑/→/↓/←/space', function (e) {
		// Stopping pane bindings when the focus is in a textarea/input/select box
		e.stopPropagation();
	}));

	var _moveItem = function(action) {
		showPane();
		var current = $('.pane .pane-actions li.pane-active');
		if (action === 'right' && current.next().length) {
			selectTab(current.next());
		}
		else if (action === 'left' && current.prev().length) {
			selectTab(current.prev());
		}
		return false;
	};

	var bindHotKeys = function(self) {
		jwerty.key('←', function (e) { e.stopPropagation(); return _moveItem('left'); });
		jwerty.key('→', function (e) { e.stopPropagation(); return _moveItem('right'); });
		jwerty.key('space', function(e) { e.stopPropagation(); togglePane(); return false; });
		jwerty.key('esc', function(e) { e.stopPropagation(); hidePane(); return false; });
	};

	return {
		start: function() {
			bindHotKeys(this);

			$('.pane .pane-container').resizable({
				handles: 'n',
				minWidth: 50
			}).on('resize', function (e, ui) {
				$(this).css('top', 'auto');
			}).on('resizestop', function() {
				$.cookie('pane-size', $(this).height());
				$('.pane-padding').height($(this).height());
			});

			$('.pane .pane-actions a').on('click', function() {
				bindActions(this);
			});

			if ($.cookie('pane-size')) {
				$('.pane .pane-container').height($.cookie('pane-size'));
				$('.pane-padding').height($.cookie('pane-size'));
			}

			app.on('errorlist.selection.activated', function() {
				showPane();
			});

			app.on('errorlist.selection.changed', function(selection) {
				errorId = selection.data('errorid');
				errorUrl = selection.data('url');
				loadError();
			});

			$(document).on('click', '.btn-claim, .btn-unclaim', function(e) {
				e.preventDefault();
				var button = $(this);
				if (button.hasClass('disabled')) return;

				button.attr('disabled', true);
				$.post(button.attr('href'), function(data) {
					var trigger = button.hasClass('btn-claim') && data.type == 'success' ? 'pane.claim': 'pane.unclaim';
					app.trigger(trigger);
					loadError();
				});
			});

			$(document).on('click', '.btn-resolve, .btn-reopen', function(e) {
				e.preventDefault();
				var button = $(this);
				if (button.hasClass('disabled')) return;

				button.attr('disabled', true);
				$.post(button.attr('href'), function(data) {
					var trigger = button.hasClass('btn-resolve') && data.type == 'success' ? 'pane.resolve': 'pane.reopen';
					app.trigger(trigger);
					hidePane();
				});
			});

			$(document).on('submit', '.tag-form', function(e) {
				e.preventDefault();
				var form = $(this);
				var field = form.find('.tag-field');
				if (field.attr('disabled')) return;

				field.attr('disabled', true);
				$.post(form.attr('action') + field.val(), function(data) {
					if (data.type == 'success')
						app.trigger('pane.tag.add', field.val());
					loadError();
				});
			});

			$(document).on('click', '.tag-delete', function(e) {
				e.preventDefault();
				var anchor = $(this);
				if (anchor.attr('disabled')) return;

				anchor.attr('disabled', true);
				$.post(anchor.attr('href') + anchor.data('tag'), function(data) {
					if (data.type == 'success')
						app.trigger('pane.tag.remove', anchor.data('tag'));
					loadError();
				});
			});

			$(document).on('submit', '.comment-form', function(e) {
				e.preventDefault();
				var form = $(this);
				var field = form.find('textarea');
				var data = form.serialize();
				if (field.attr('disabled')) return;

				field.attr('disabled', true);
				$.post(form.attr('action'), data, function(data) {
					if (data.type == 'success')
						loadError();
				});
			});

		},
		stop: function() { }
	};
});

Triage.modules.pane.autoRegister = true;
