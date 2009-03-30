/*
 * Copyright (c) 2008-2009 Brad Taylor <brad@getcoded.net>
 *
 * Permission is hereby granted, free of charge, to any person obtaining 
 * a copy of this software and associated documentation files (the 
 * "Software"), to deal in the Software without restriction, including 
 * without limitation the rights to use, copy, modify, merge, publish, 
 * distribute, sublicense, and/or sell copies of the Software, and to 
 * permit persons to whom the Software is furnished to do so, subject to 
 * the following conditions: 
 *  
 * The above copyright notice and this permission notice shall be 
 * included in all copies or substantial portions of the Software. 
 *  
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, 
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE 
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION 
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. 
*/

function createTasksGrid(target_id, url, iteration_days) {
    var fields = [
        { name: 'id', type: 'string' }, { name: 'title', type: 'string' },
        { name: 'component', type: 'string' }, { name: 'assigned_to', type: 'string' },
        { name: 'submitted_by', type: 'string' }, { name: 'status', type: 'string' },
        { name: 'estimated_hours', type: 'int' },
    ];
    for (var i = 1; i < iteration_days + 1; i++) {
        fields.push({ name: 'day_' + i, type: 'int' });
    }

    var columns = [
        { header: "Id", width: 65, dataIndex: 'id', 
          summaryRenderer: function(v, params, data) {
                return 'Total:';
          },
        },
        { header: "Title", width: 500, dataIndex: 'title', summaryType: 'count',
          summaryRenderer: function(v, params, data) {
                return ((v === 0 || v > 1) ? v + ' Tasks' : '1 Task');
          },
        },
        { header: "Component", width: 70, dataIndex: 'component' },
        { header: "Assigned To", width: 75, dataIndex: 'assigned_to' },
        { header: "Submitted By", width: 75, dataIndex: 'submitted_by', hidden: true },
        { header: "Status", width: 70, dataIndex: 'status' },
        { header: "Est", width: 25, dataIndex: 'estimated_hours', summaryType: 'sum' },
    ];
    for (var i = 1; i < iteration_days + 1; i++) {
        columns.push({
            header: i.toString(), width: 25, 
            dataIndex: 'day_' + i, hideable: false, summaryType: 'sum'
        });
    }

    var grid = new Ext.grid.GridPanel({
        store: new Ext.data.GroupingStore({
            reader: new Ext.data.ArrayReader({}, fields),
            url: url,
            autoLoad: true,
            sortInfo: { field: 'status', direction: "asc" },
            groupField: 'component',
        }),
        columns: columns, stripeRows: true,
        width: "100%", height: 500,
        loadMask: true,
        view: new Ext.grid.GroupingView({
            showGroupName: true, hideGroupedColumn: true
        }),
        plugins: new Ext.grid.GroupSummary(),
    });
    grid.getColumnModel().defaultSortable = true;
    grid.render(target_id);
    return grid;
}

function createTeamMemberGrid(target_id, iteration_days) {
    var fields = new Array ();
    var columns = new Array ();

    fields.push({ name: 'team_member', type: 'string' });
    for (var i = 1; i < iteration_days + 1; i++) {
        fields.push({ name: 'day_' + i.toString(), type: 'string' });
    }

    columns.push({ header: 'Team Member', width: 80, dataIndex: 'team_member' });
    for (var i = 1; i < iteration_days + 1; i++) {
        columns.push({
		header: i.toString(), width: 25, dataIndex: ("day_" + i),
		resizable: false, hideable: false,
	});
    }

    var grid = new Ext.grid.GridPanel({
        store: new Ext.data.SimpleStore({ fields: fields }),
        columns: columns, stripeRows: true,
        autoWidth: true, autoHeight: true,
        loadMask: true,
    });

    grid.getColumnModel().defaultSortable = true;
    grid.render(target_id);
    return grid;
}
