/*global Triage: true, jwerty: true*/

Triage.modules.errorList = (function($, app) {
	"use strict";

	var currentSelection = null;

	var changeSelection = function(selected) {
		selected = $(selected);

		selected.siblings().removeClass('error-active');
		selected.addClass('error-active');

		if (selected.is(':first-child')) {
			$('body').scrollTop(0);
		}
		else if (selected.is(':last-child')) {
			$('body').scrollTop($('body').height());
		}
		else {
			if (selected.offset().top < $('body').scrollTop()) {
				$('body').scrollTop(selected.offset().top);
			}

			if (selected.offset().top > $('.pane').offset().top) {
				$('body').scrollTop($('body').scrollTop() + selected.height());
			}
		}

		currentSelection = selected.data('errorid');
		app.trigger('errorlist.selection.changed', selected);
	};

	var activateSelection = function() {
		app.trigger('errorlist.selection.activated');
	};

	var _moveItem = function(action) {
		action = action || 'down';
		var current = $('.error-list tr.error-active');

		if (!current.length) {
			changeSelection($('.error-list tr:first-child'));
		}
		else if (action === 'down' && current.next().length) {
			changeSelection(current.next());
		}
		else if (action === 'up' && current.prev().length) {
			changeSelection(current.prev());
		}

		return false;
	};

	var bindHotKeys = function(self) {
		jwerty.key('↑', function (e) { e.stopPropagation(); return _moveItem('up'); });
		jwerty.key('↓', function (e) { e.stopPropagation(); return _moveItem('down'); });
	};

	return {
		start: function() {
			bindHotKeys(this);

			$('.error-list').on('click', '.multiselect', function(e)  {
				e.stopPropagation();
			});

			$('.error-list').on('click', '.error-list tbody tr', function() {
				changeSelection(this);
				activateSelection();
			});

			app.on('pane.tag.remove', function(tag) {
				$('.label-'+tag).fadeOut();
			});

			app.on('error.viewed', function(errorId) {
				var node = $('#error-'+errorId);
				var unseen = node.hasClass('unseen');
				node.removeClass('unseen').addClass('seen');

				if (unseen) {
					app.trigger('error.seen', errorId);
				}
			});

			app.on('pane.claim', function() {
				$('.error-list tr.error-active td.date').append(
					'<span class="claimed-by"><i class="icon-star"></i>&nbsp;You</span>'
				);
			});

			app.on('pane.unclaim', function() {
				$('.error-list tr.error-active .claimed-by').fadeOut(function () { $(this).remove(); });
			});

			app.on('pane.resolve', function() {
				$('.error-list tr.error-active').fadeOut(function () { $(this).remove(); });
			});

			app.on('pane.reopen', function() {
				$('.error-list tr.error-active').fadeOut(function () { $(this).remove(); });
			});

			app.on('pane.tag.add', function(tag) {
				$('<span class="label label-' + tag + '">' + tag + '</span>').appendTo(
					$('.error-list tr.error-active .error .detail-tags')
				);
			});

			app.on('pane.tag.remove', function(tag) {
				$('.error-list tr.error-active .error .detail-tags .label-' + tag).fadeOut(function () { $(this).remove(); });
			});
		},
		stop: function() { },
		currentHash: null
	};
});

Triage.modules.errorList.autoRegister = true;
